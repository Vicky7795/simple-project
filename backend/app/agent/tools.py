import json
import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from db.session import SessionLocal
import db.models as models
from .llm_client import get_llm

# Pydantic schemas for tool inputs

class LogInteractionInput(BaseModel):
    hcp_name: str = Field(description="Name of the Healthcare Professional (e.g. Dr. Anil Sharma)")
    interaction_type: str = Field(description="Type of interaction: visit, call, email, or conference")
    topics_discussed: List[str] = Field(default=[], description="Topics discussed during the interaction")
    products_discussed: List[str] = Field(default=[], description="Products/Drugs discussed")
    sentiment: str = Field(default="neutral", description="Rep sentiment observation: positive, neutral, or negative")
    follow_up_required: bool = Field(default=False, description="Whether follow up is required")
    follow_up_date: Optional[str] = Field(default=None, description="ISO format date (YYYY-MM-DD) for follow up")
    samples_distributed: Optional[Dict[str, int]] = Field(default=None, description="Dictionary of product name keys and quantity values")
    raw_input: Optional[str] = Field(default=None, description="Original raw chat input from the rep")

class EditInteractionInput(BaseModel):
    interaction_id: int = Field(description="The ID of the interaction to edit")
    hcp_name: Optional[str] = Field(default=None, description="Update the HCP name")
    interaction_type: Optional[str] = Field(default=None, description="Update interaction type")
    topics_discussed: Optional[List[str]] = Field(default=None, description="Update topics list")
    products_discussed: Optional[List[str]] = Field(default=None, description="Update products list")
    sentiment: Optional[str] = Field(default=None, description="Update sentiment tag")
    follow_up_required: Optional[bool] = Field(default=None, description="Update follow up flag")
    follow_up_date: Optional[str] = Field(default=None, description="Update follow up date (YYYY-MM-DD)")
    samples_distributed: Optional[Dict[str, int]] = Field(default=None, description="Update samples dictionary")

class LookupHcpInput(BaseModel):
    name_query: str = Field(description="Fuzzy name or specialty query for lookup")

class ScheduleFollowupInput(BaseModel):
    interaction_id: int = Field(description="The ID of the interaction to associate follow-up with")
    follow_up_date: str = Field(description="The follow up date in YYYY-MM-DD format")

class SummarizeHistoryInput(BaseModel):
    hcp_id: int = Field(description="The ID of the Healthcare Professional (HCP)")

# Tools implementation

@tool("log_interaction", args_schema=LogInteractionInput)
def log_interaction(
    hcp_name: str,
    interaction_type: str,
    topics_discussed: List[str] = [],
    products_discussed: List[str] = [],
    sentiment: str = "neutral",
    follow_up_required: bool = False,
    follow_up_date: Optional[str] = None,
    samples_distributed: Optional[Dict[str, int]] = None,
    raw_input: Optional[str] = None
) -> Dict[str, Any]:
    """Logs a new interaction with an HCP in the database. Resolves HCP name and generates a summary."""
    db = SessionLocal()
    try:
        # 1. Resolve HCP by name
        clean_name = hcp_name.replace("Dr.", "").strip()
        hcp = db.query(models.HCP).filter(models.HCP.name.like(f"%{clean_name}%")).first()
        
        if not hcp:
            # Create new HCP if not found
            hcp = models.HCP(
                name=hcp_name if hcp_name.startswith("Dr.") else f"Dr. {hcp_name}",
                specialty="General Medicine",
                hospital_affiliation="General Hospital",
                preferred_channel=interaction_type if interaction_type in ["call", "visit", "email"] else "visit",
                notes="Created automatically via AI Agent interaction log."
            )
            db.add(hcp)
            db.flush()
            hcp_created = True
        else:
            hcp_created = False

        # 2. Parse dates
        f_date = None
        if follow_up_required and follow_up_date:
            try:
                f_date = datetime.datetime.strptime(follow_up_date, "%Y-%m-%d").date()
            except ValueError:
                # Fallback to 7 days from now if date parsing fails
                f_date = datetime.date.today() + datetime.timedelta(days=7)

        # 3. Generate summary using LLM if not provided
        summary_text = ""
        if raw_input:
            llm = get_llm(context_model=False)
            prompt = (
                f"You are a sales assistant. Write a short, professional, 1-2 sentence summary of this interaction log for "
                f"the CRM. Raw text: '{raw_input}'. Focus on key talking points and requests."
            )
            try:
                response = llm.invoke(prompt)
                summary_text = response.content.strip()
            except Exception as e:
                summary_text = f"Interaction logged with {hcp.name}. Topics: {', '.join(topics_discussed)}."
        else:
            summary_text = f"Logged a {interaction_type} with {hcp.name}. Topics: {', '.join(topics_discussed)}."

        # 4. Insert Interaction
        interaction = models.Interaction(
            hcp_id=hcp.id,
            user_id=1,  # Default user ID
            interaction_type=interaction_type,
            interaction_date=datetime.datetime.utcnow(),
            channel=interaction_type,
            topics_discussed=topics_discussed,
            products_discussed=products_discussed,
            sentiment=sentiment,
            summary=summary_text,
            raw_input=raw_input or f"Form submission for {hcp.name}",
            source="chat" if raw_input else "form",
            follow_up_required=follow_up_required,
            follow_up_date=f_date,
            samples_distributed=samples_distributed or {}
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        return {
            "success": True,
            "message": f"Successfully logged interaction with {hcp.name}.",
            "interaction_id": interaction.id,
            "hcp": {
                "id": hcp.id,
                "name": hcp.name,
                "specialty": hcp.specialty,
                "affiliation": hcp.hospital_affiliation,
                "created": hcp_created
            },
            "details": {
                "type": interaction.interaction_type,
                "topics": interaction.topics_discussed,
                "sentiment": interaction.sentiment,
                "summary": interaction.summary,
                "follow_up_required": interaction.follow_up_required,
                "follow_up_date": str(interaction.follow_up_date) if interaction.follow_up_date else None,
                "samples": interaction.samples_distributed
            }
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@tool("edit_interaction", args_schema=EditInteractionInput)
def edit_interaction(
    interaction_id: int,
    hcp_name: Optional[str] = None,
    interaction_type: Optional[str] = None,
    topics_discussed: Optional[List[str]] = None,
    products_discussed: Optional[List[str]] = None,
    sentiment: Optional[str] = None,
    follow_up_required: Optional[bool] = None,
    follow_up_date: Optional[str] = None,
    samples_distributed: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """Edits an existing interaction's fields in the database and creates an audit edit history record."""
    db = SessionLocal()
    try:
        interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
        if not interaction:
            return {"success": False, "error": f"Interaction with ID {interaction_id} not found."}

        updates_made = []
        
        # Helper to log audits and update fields
        def update_field(field_name: str, new_val: Any, current_val: Any, is_date=False):
            if new_val is not None and new_val != current_val:
                db_val = new_val
                if is_date and new_val:
                    db_val = datetime.datetime.strptime(new_val, "%Y-%m-%d").date()
                
                # Create audit log
                audit = models.InteractionEdit(
                    interaction_id=interaction.id,
                    edited_field=field_name,
                    old_value=str(current_val),
                    new_value=str(new_val),
                    edited_by=1  # Default user ID
                )
                db.add(audit)
                setattr(interaction, field_name, db_val)
                updates_made.append(field_name)

        if hcp_name:
            clean_name = hcp_name.replace("Dr.", "").strip()
            hcp = db.query(models.HCP).filter(models.HCP.name.like(f"%{clean_name}%")).first()
            if hcp:
                update_field("hcp_id", hcp.id, interaction.hcp_id)
            else:
                # Create new HCP if they don't exist
                new_hcp = models.HCP(
                    name=hcp_name if hcp_name.startswith("Dr.") else f"Dr. {hcp_name}",
                    specialty="General Medicine",
                    hospital_affiliation="General Hospital",
                    notes="Created automatically via interaction edit."
                )
                db.add(new_hcp)
                db.flush()
                update_field("hcp_id", new_hcp.id, interaction.hcp_id)

        update_field("interaction_type", interaction_type, interaction.interaction_type)
        update_field("topics_discussed", topics_discussed, interaction.topics_discussed)
        update_field("products_discussed", products_discussed, interaction.products_discussed)
        update_field("sentiment", sentiment, interaction.sentiment)
        update_field("follow_up_required", follow_up_required, interaction.follow_up_required)
        update_field("follow_up_date", follow_up_date, interaction.follow_up_date, is_date=True)
        update_field("samples_distributed", samples_distributed, interaction.samples_distributed)

        if updates_made:
            # Re-generate summary to reflect updates
            llm = get_llm(context_model=False)
            prompt = (
                f"Write a short, professional, 1-2 sentence summary of this UPDATED interaction log for a Healthcare Professional. "
                f"HCP ID: {interaction.hcp_id}, Type: {interaction.interaction_type}, Topics: {interaction.topics_discussed}, "
                f"Products: {interaction.products_discussed}, Sentiment: {interaction.sentiment}, Samples: {interaction.samples_distributed}."
            )
            try:
                response = llm.invoke(prompt)
                interaction.summary = response.content.strip()
            except Exception:
                interaction.summary = f"Updated: Logged {interaction.interaction_type} with HCP ID {interaction.hcp_id}. Topics: {interaction.topics_discussed}."
            
            db.commit()
            db.refresh(interaction)
            return {
                "success": True,
                "message": f"Successfully updated interaction {interaction_id}.",
                "updated_fields": updates_made,
                "details": {
                    "type": interaction.interaction_type,
                    "topics": interaction.topics_discussed,
                    "sentiment": interaction.sentiment,
                    "summary": interaction.summary,
                    "follow_up_required": interaction.follow_up_required,
                    "follow_up_date": str(interaction.follow_up_date) if interaction.follow_up_date else None,
                    "samples": interaction.samples_distributed
                }
            }
        else:
            return {"success": True, "message": "No changes were detected.", "updated_fields": []}
            
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@tool("lookup_hcp", args_schema=LookupHcpInput)
def lookup_hcp(name_query: str) -> Dict[str, Any]:
    """Fuzzy-searches Healthcare Professionals (HCPs) by name or specialty, and retrieves their recent interactions."""
    db = SessionLocal()
    try:
        clean_query = name_query.replace("Dr.", "").strip()
        hcps = db.query(models.HCP).filter(
            (models.HCP.name.like(f"%{clean_query}%")) | 
            (models.HCP.specialty.like(f"%{clean_query}%"))
        ).all()

        results = []
        for hcp in hcps:
            # Get last 3 interactions
            recent = db.query(models.Interaction).filter(
                models.Interaction.hcp_id == hcp.id
            ).order_by(models.Interaction.interaction_date.desc()).limit(3).all()

            interactions_list = []
            for inter in recent:
                interactions_list.append({
                    "id": inter.id,
                    "type": inter.interaction_type,
                    "date": str(inter.interaction_date.date()),
                    "topics": inter.topics_discussed,
                    "sentiment": inter.sentiment,
                    "summary": inter.summary
                })

            results.append({
                "id": hcp.id,
                "name": hcp.name,
                "specialty": hcp.specialty,
                "hospital": hcp.hospital_affiliation,
                "email": hcp.email,
                "phone": hcp.phone,
                "preferred_channel": hcp.preferred_channel,
                "notes": hcp.notes,
                "recent_interactions": interactions_list
            })

        return {
            "success": True,
            "count": len(results),
            "matches": results
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@tool("schedule_followup", args_schema=ScheduleFollowupInput)
def schedule_followup(interaction_id: int, follow_up_date: str) -> Dict[str, Any]:
    """Schedules a follow-up for a specific interaction log by updating its follow-up flags and date."""
    db = SessionLocal()
    try:
        interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
        if not interaction:
            return {"success": False, "error": f"Interaction with ID {interaction_id} not found."}

        try:
            f_date = datetime.datetime.strptime(follow_up_date, "%Y-%m-%d").date()
        except ValueError:
            return {"success": False, "error": f"Invalid date format: {follow_up_date}. Please use YYYY-MM-DD."}

        # Log change to audit
        audit = models.InteractionEdit(
            interaction_id=interaction.id,
            edited_field="follow_up_date",
            old_value=str(interaction.follow_up_date),
            new_value=str(follow_up_date),
            edited_by=1
        )
        db.add(audit)
        
        interaction.follow_up_required = True
        interaction.follow_up_date = f_date
        db.commit()

        return {
            "success": True,
            "message": f"Successfully scheduled follow-up for interaction {interaction_id} on {follow_up_date}.",
            "details": {
                "interaction_id": interaction.id,
                "follow_up_required": interaction.follow_up_required,
                "follow_up_date": str(interaction.follow_up_date)
            }
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@tool("summarize_interaction_history", args_schema=SummarizeHistoryInput)
def summarize_interaction_history(hcp_id: int) -> Dict[str, Any]:
    """Retrieves all past interactions for an HCP and uses the LLM to generate a relationship summary."""
    db = SessionLocal()
    try:
        hcp = db.query(models.HCP).filter(models.HCP.id == hcp_id).first()
        if not hcp:
            return {"success": False, "error": f"HCP with ID {hcp_id} not found."}

        interactions = db.query(models.Interaction).filter(
            models.Interaction.hcp_id == hcp_id
        ).order_by(models.Interaction.interaction_date.desc()).all()

        if not interactions:
            return {
                "success": True,
                "hcp_name": hcp.name,
                "summary": "No interaction history found for this Healthcare Professional."
            }

        # Build history log for the LLM
        history_logs = []
        for i, inter in enumerate(interactions):
            history_logs.append(
                f"[{i+1}] Date: {inter.interaction_date.date()}, Type: {inter.interaction_type}, "
                f"Topics: {inter.topics_discussed}, Products: {inter.products_discussed}, "
                f"Sentiment: {inter.sentiment}, Summary: {inter.summary}, "
                f"Samples Given: {inter.samples_distributed}"
            )
        
        history_text = "\n".join(history_logs)

        # Generate summary using the context model (llama-3.3-70b-versatile) for reasoning
        llm = get_llm(context_model=True)
        prompt = (
            f"You are a sales intelligence assistant. Here is the interaction history between a sales representative "
            f"and the doctor {hcp.name} ({hcp.specialty} affiliated with {hcp.hospital_affiliation}).\n\n"
            f"History:\n{history_text}\n\n"
            f"Generate a professional 'relationship summary' for the representative's upcoming visit. "
            f"Briefly outline: 1. Key talking points discussed in past meetings, 2. Overall sentiment trend, "
            f"3. Any outstanding requests or scheduled follow-ups, and 4. Recent samples provided. "
            f"Keep the summary concise, actionable, and formatted with clean bullet points."
        )

        try:
            response = llm.invoke(prompt)
            summary_result = response.content.strip()
        except Exception as e:
            summary_result = f"Error generating summary: {str(e)}. Total interactions in DB: {len(interactions)}."

        return {
            "success": True,
            "hcp_name": hcp.name,
            "hcp_specialty": hcp.specialty,
            "total_interactions": len(interactions),
            "summary": summary_result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        db.close()

# List of all tools for LangGraph exports
ALL_TOOLS = [
    log_interaction,
    edit_interaction,
    lookup_hcp,
    schedule_followup,
    summarize_interaction_history
]

# Map of tool name to actual function for manual execution
TOOLS_MAP = {
    "log_interaction": log_interaction,
    "edit_interaction": edit_interaction,
    "lookup_hcp": lookup_hcp,
    "schedule_followup": schedule_followup,
    "summarize_interaction_history": summarize_interaction_history
}
