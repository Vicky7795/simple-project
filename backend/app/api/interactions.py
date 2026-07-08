from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from db.session import get_db
import db.models as models
import schemas
from agent.llm_client import get_llm

router = APIRouter(prefix="/interactions", tags=["Interactions"])

@router.get("", response_model=List[schemas.InteractionResponse])
def get_interactions(
    hcp_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(models.Interaction)
    if hcp_id:
        query = query.filter(models.Interaction.hcp_id == hcp_id)
    if user_id:
        query = query.filter(models.Interaction.user_id == user_id)
    return query.order_by(models.Interaction.interaction_date.desc()).all()

@router.post("", response_model=schemas.InteractionResponse, status_code=201)
def create_interaction(data: schemas.InteractionCreate, db: Session = Depends(get_db)):
    # Verify HCP exists
    hcp = db.query(models.HCP).filter(models.HCP.id == data.hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail=f"HCP with ID {data.hcp_id} not found.")

    # Populate summary if missing, using Groq LLM
    summary_text = data.summary
    if not summary_text:
        llm = get_llm(context_model=False)
        prompt = (
            f"Write a short, professional, 1-2 sentence summary of this structured interaction log for the CRM. "
            f"Doctor: {hcp.name}, Type: {data.interaction_type}, Topics: {data.topics_discussed}, "
            f"Products: {data.products_discussed}, Sentiment: {data.sentiment}, Samples: {data.samples_distributed}."
        )
        try:
            response = llm.invoke(prompt)
            summary_text = response.content.strip()
        except Exception:
            summary_text = f"Logged a {data.interaction_type} with {hcp.name}. Topics discussed: {', '.join(data.topics_discussed)}."

    db_inter = models.Interaction(
        hcp_id=data.hcp_id,
        user_id=1,  # Default User ID
        interaction_type=data.interaction_type,
        interaction_date=data.interaction_date or datetime.datetime.utcnow(),
        channel=data.channel or data.interaction_type,
        topics_discussed=data.topics_discussed,
        products_discussed=data.products_discussed,
        sentiment=data.sentiment,
        summary=summary_text,
        raw_input=data.raw_input or f"Form submission for {hcp.name}",
        source=data.source,
        follow_up_required=data.follow_up_required,
        follow_up_date=data.follow_up_date,
        samples_distributed=data.samples_distributed or {}
    )
    db.add(db_inter)
    db.commit()
    db.refresh(db_inter)
    return db_inter

@router.get("/{inter_id}", response_model=schemas.InteractionResponse)
def get_interaction(inter_id: int, db: Session = Depends(get_db)):
    inter = db.query(models.Interaction).filter(models.Interaction.id == inter_id).first()
    if not inter:
        raise HTTPException(status_code=404, detail=f"Interaction with ID {inter_id} not found.")
    return inter

@router.put("/{inter_id}", response_model=schemas.InteractionResponse)
def update_interaction(inter_id: int, data: schemas.InteractionUpdate, db: Session = Depends(get_db)):
    inter = db.query(models.Interaction).filter(models.Interaction.id == inter_id).first()
    if not inter:
        raise HTTPException(status_code=404, detail=f"Interaction with ID {inter_id} not found.")

    updates = data.model_dump(exclude_unset=True)
    
    # Helper to update fields and record audit history
    for field, new_val in updates.items():
        current_val = getattr(inter, field)
        if new_val != current_val:
            # Create audit history log
            audit = models.InteractionEdit(
                interaction_id=inter.id,
                edited_field=field,
                old_value=str(current_val),
                new_value=str(new_val),
                edited_by=1
            )
            db.add(audit)
            setattr(inter, field, new_val)

    # Regenerate summary if key details changed
    if any(k in updates for k in ["topics_discussed", "products_discussed", "sentiment", "samples_distributed"]):
        hcp = db.query(models.HCP).filter(models.HCP.id == inter.hcp_id).first()
        llm = get_llm(context_model=False)
        prompt = (
            f"Write a short, professional, 1-2 sentence summary of this UPDATED structured interaction log for the CRM. "
            f"Doctor: {hcp.name if hcp else 'HCP'}, Type: {inter.interaction_type}, Topics: {inter.topics_discussed}, "
            f"Products: {inter.products_discussed}, Sentiment: {inter.sentiment}, Samples: {inter.samples_distributed}."
        )
        try:
            response = llm.invoke(prompt)
            inter.summary = response.content.strip()
        except Exception:
            pass

    db.commit()
    db.refresh(inter)
    return inter
