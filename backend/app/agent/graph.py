import json
import datetime
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .llm_client import get_llm
from .prompts import INTENT_ROUTER_PROMPT, ENTITY_EXTRACTION_PROMPT, RESPONSE_FORMATTER_PROMPT
from .tools import TOOLS_MAP

# Define State
class AgentState(TypedDict):
    messages: List[Dict[str, str]]    # list of {"role": "user"|"assistant", "content": "..."}
    intent: str                        # classified intent
    extracted_data: Dict[str, Any]     # parsed JSON data from extraction
    tool_result: Dict[str, Any]        # result returned from tool execution
    thread_id: str                     # conversation thread
    user_id: int                       # user ID executing
    reply: str                         # final agent reply
    tool_used: Optional[str]           # name of tool executed if any
    interaction_id: Optional[int]      # interaction ID if logged/edited

# Define nodes

def classify_intent_node(state: AgentState) -> Dict[str, Any]:
    """Node to classify the user's intent from the last message."""
    messages = state["messages"]
    last_user_message = [m for m in messages if m["role"] == "user"][-1]["content"]
    
    llm = get_llm(context_model=False)
    system_message = {"role": "system", "content": INTENT_ROUTER_PROMPT}
    user_message = {"role": "user", "content": f"Message: {last_user_message}"}
    
    try:
        response = llm.invoke([system_message, user_message])
        intent = response.content.strip().lower()
        # Clean any extra wrapper or quotes
        intent = intent.replace("'", "").replace('"', "").strip()
        
        # Valid intents list
        valid_intents = [
            "log_interaction",
            "edit_interaction",
            "lookup_hcp",
            "schedule_followup",
            "summarize_history",
            "general_query"
        ]
        if intent not in valid_intents:
            intent = "general_query"
    except Exception as e:
        print(f"Error in classify_intent_node: {e}")
        intent = "general_query"
        
    return {"intent": intent}

def extract_entities_node(state: AgentState) -> Dict[str, Any]:
    """Node to extract entities from the user's message for tool inputs."""
    intent = state["intent"]
    if intent == "general_query":
        return {"extracted_data": {}}

    messages = state["messages"]
    last_user_message = [m for m in messages if m["role"] == "user"][-1]["content"]
    current_date = datetime.date.today().strftime("%Y-%m-%d")
    
    # Estimate next Friday for the prompt example
    next_friday = datetime.date.today()
    while next_friday.weekday() != 4:
        next_friday += datetime.timedelta(days=1)
    estimated_next_friday = next_friday.strftime("%Y-%m-%d")

    llm = get_llm(context_model=False)
    
    # Groq supports JSON mode if specified, but let's prompt clearly and try to parse
    system_prompt = ENTITY_EXTRACTION_PROMPT.format(
        current_date=current_date,
        estimated_next_friday=estimated_next_friday
    )
    
    system_message = {"role": "system", "content": system_prompt}
    user_message = {"role": "user", "content": f"Extract from this message: '{last_user_message}'"}
    
    extracted_data = {}
    try:
        # Call Groq with json_object format if supported, or just clean string
        response = llm.invoke(
            [system_message, user_message],
            response_format={"type": "json_object"}
        )
        content = response.content.strip()
        # Clean potential markdown wrapping
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        extracted_data = json.loads(content)
    except Exception as e:
        print(f"Error in extract_entities_node: {e}")
        # Try a regex-less fallback or return empty
        extracted_data = {}

    # Append raw_input for log_interaction tool
    extracted_data["raw_input"] = last_user_message
    return {"extracted_data": extracted_data}

def call_tool_node(state: AgentState) -> Dict[str, Any]:
    """Node to execute the appropriate database tool."""
    intent = state["intent"]
    extracted = state["extracted_data"]
    
    if intent == "general_query":
        return {"tool_result": {"success": True, "message": "General conversational query."}, "tool_used": None}

    tool_used = None
    tool_result = {"success": False, "error": "No matching tool found."}

    # Helper: resolve HCP ID if we have hcp_name but the tool requires hcp_id
    def get_hcp_id_by_name(name: str) -> Optional[int]:
        if not name:
            return None
        from db.session import SessionLocal
        import db.models as models
        db = SessionLocal()
        try:
            clean_name = name.replace("Dr.", "").strip()
            hcp = db.query(models.HCP).filter(models.HCP.name.like(f"%{clean_name}%")).first()
            return hcp.id if hcp else None
        except Exception:
            return None
        finally:
            db.close()

    # Helper: find last interaction ID for this user/session to edit or schedule followup
    def get_last_interaction_id() -> Optional[int]:
        from db.session import SessionLocal
        import db.models as models
        db = SessionLocal()
        try:
            inter = db.query(models.Interaction).order_by(models.Interaction.id.desc()).first()
            return inter.id if inter else None
        except Exception:
            return None
        finally:
            db.close()

    try:
        if intent == "log_interaction":
            tool_used = "log_interaction"
            tool_func = TOOLS_MAP[tool_used]
            # Map extracted data to tool arguments
            args = {
                "hcp_name": extracted.get("hcp_name") or "Unknown Doctor",
                "interaction_type": extracted.get("interaction_type") or "visit",
                "topics_discussed": extracted.get("topics_discussed") or [],
                "products_discussed": extracted.get("products_discussed") or [],
                "sentiment": extracted.get("sentiment") or "neutral",
                "follow_up_required": extracted.get("follow_up_required") or False,
                "follow_up_date": extracted.get("follow_up_date"),
                "samples_distributed": extracted.get("samples_distributed"),
                "raw_input": extracted.get("raw_input")
            }
            tool_result = tool_func.invoke(args)

        elif intent == "edit_interaction":
            tool_used = "edit_interaction"
            tool_func = TOOLS_MAP[tool_used]
            
            # Find which interaction to edit
            # If user message mentions an ID, use it. Otherwise, assume last logged interaction.
            raw_msg = extracted.get("raw_input", "")
            # Simple regex search for numbers
            import re
            numbers = re.findall(r'\b\d+\b', raw_msg)
            inter_id = int(numbers[0]) if numbers else get_last_interaction_id()
            
            if not inter_id:
                tool_result = {"success": False, "error": "Could not identify which interaction to edit. Please specify the ID."}
            else:
                args = {"interaction_id": inter_id}
                # Map optional update fields
                if extracted.get("hcp_name"):
                    args["hcp_name"] = extracted["hcp_name"]
                if extracted.get("interaction_type"):
                    args["interaction_type"] = extracted["interaction_type"]
                if extracted.get("topics_discussed"):
                    args["topics_discussed"] = extracted["topics_discussed"]
                if extracted.get("products_discussed"):
                    args["products_discussed"] = extracted["products_discussed"]
                if extracted.get("sentiment"):
                    args["sentiment"] = extracted["sentiment"]
                if extracted.get("follow_up_required") is not None:
                    args["follow_up_required"] = extracted["follow_up_required"]
                if extracted.get("follow_up_date"):
                    args["follow_up_date"] = extracted["follow_up_date"]
                if extracted.get("samples_distributed"):
                    args["samples_distributed"] = extracted["samples_distributed"]
                
                tool_result = tool_func.invoke(args)

        elif intent == "lookup_hcp":
            tool_used = "lookup_hcp"
            tool_func = TOOLS_MAP[tool_used]
            args = {"name_query": extracted.get("hcp_name") or extracted.get("raw_input", "")}
            tool_result = tool_func.invoke(args)

        elif intent == "schedule_followup":
            tool_used = "schedule_followup"
            tool_func = TOOLS_MAP[tool_used]
            
            raw_msg = extracted.get("raw_input", "")
            import re
            numbers = re.findall(r'\b\d+\b', raw_msg)
            inter_id = int(numbers[0]) if numbers else get_last_interaction_id()
            
            f_date = extracted.get("follow_up_date")
            if not f_date:
                # Default to next week if not extracted
                f_date = (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
                
            if not inter_id:
                tool_result = {"success": False, "error": "Could not identify which interaction to schedule follow-up for."}
            else:
                args = {"interaction_id": inter_id, "follow_up_date": f_date}
                tool_result = tool_func.invoke(args)

        elif intent == "summarize_history":
            tool_used = "summarize_interaction_history"
            tool_func = TOOLS_MAP[tool_used]
            
            hcp_id = get_hcp_id_by_name(extracted.get("hcp_name"))
            if not hcp_id:
                # Try finding any HCP in DB as fallback
                from db.session import SessionLocal
                import db.models as models
                db = SessionLocal()
                hcp = db.query(models.HCP).first()
                hcp_id = hcp.id if hcp else None
                db.close()
                
            if not hcp_id:
                tool_result = {"success": False, "error": "HCP not found in database to summarize history."}
            else:
                args = {"hcp_id": hcp_id}
                tool_result = tool_func.invoke(args)

    except Exception as e:
        print(f"Error running tool {tool_used}: {e}")
        tool_result = {"success": False, "error": str(e)}

    return {"tool_result": tool_result, "tool_used": tool_used}

def format_response_node(state: AgentState) -> Dict[str, Any]:
    """Node to format a natural conversational response to the user."""
    intent = state["intent"]
    tool_used = state["tool_used"]
    tool_res = state["tool_result"]
    messages = state["messages"]
    last_user_message = [m for m in messages if m["role"] == "user"][-1]["content"]
    
    llm = get_llm(context_model=False)
    
    if intent == "general_query":
        # Let LLM reply directly in a conversational manner
        prompt = (
            f"You are a sales assistant for an HCP CRM. The user says: '{last_user_message}'. "
            f"Provide a helpful, professional, and friendly response. You can explain how to log interactions "
            f"('Met Dr. Sharma, discussed Glynase'), look up HCP history, or schedule followups."
        )
        try:
            response = llm.invoke(prompt)
            reply = response.content.strip()
        except Exception as e:
            reply = f"Hello! How can I help you log or manage your HCP interactions today?"
    else:
        # Formulate response based on tool result
        system_prompt = RESPONSE_FORMATTER_PROMPT.format(
            user_message=last_user_message,
            intent=intent,
            tool_name=tool_used or "None",
            tool_result=json.dumps(tool_res)
        )
        try:
            response = llm.invoke([{"role": "system", "content": system_prompt}])
            reply = response.content.strip()
        except Exception as e:
            if tool_res.get("success"):
                reply = f"Done! {tool_res.get('message', 'Action completed successfully.')}"
            else:
                reply = f"Sorry, I encountered an error: {tool_res.get('error', 'Unknown database error.')}"

    # Extract interaction_id if present
    interaction_id = None
    if tool_res.get("success") and "interaction_id" in tool_res:
        interaction_id = tool_res["interaction_id"]
    elif tool_res.get("success") and "details" in tool_res and "interaction_id" in tool_res["details"]:
        interaction_id = tool_res["details"]["interaction_id"]

    return {
        "reply": reply,
        "interaction_id": interaction_id,
        "messages": messages + [{"role": "assistant", "content": reply}]
    }

# Build LangGraph StateGraph
def get_agent_graph():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("classify_intent", classify_intent_node)
    workflow.add_node("extract_entities", extract_entities_node)
    workflow.add_node("call_tool", call_tool_node)
    workflow.add_node("format_response", format_response_node)

    # Set Edges
    workflow.set_entry_point("classify_intent")
    workflow.add_edge("classify_intent", "extract_entities")
    workflow.add_edge("extract_entities", "call_tool")
    workflow.add_edge("call_tool", "format_response")
    workflow.add_edge("format_response", END)

    # Memory Saver Checkpointer for multi-turn thread memory
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

# Compiled agent instance
agent_graph = get_agent_graph()

def run_agent(thread_id: str, user_id: int, user_message: str) -> Dict[str, Any]:
    """Runs the LangGraph agent for a given thread_id and message."""
    config = {"configurable": {"thread_id": thread_id}}
    
    # Check if there is history in checkpointer
    # If not, initialize state
    state = agent_graph.get_state(config)
    
    if not state or not state.values:
        initial_state = {
            "messages": [{"role": "user", "content": user_message}],
            "intent": "",
            "extracted_data": {},
            "tool_result": {},
            "thread_id": thread_id,
            "user_id": user_id,
            "reply": "",
            "tool_used": None,
            "interaction_id": None
        }
    else:
        current_messages = state.values.get("messages", [])
        initial_state = {
            **state.values,
            "messages": current_messages + [{"role": "user", "content": user_message}],
            "intent": "",
            "extracted_data": {},
            "tool_result": {},
            "reply": "",
            "tool_used": None,
            "interaction_id": None
        }
        
    final_output = agent_graph.invoke(initial_state, config)
    
    return {
        "reply": final_output["reply"],
        "intent": final_output["intent"],
        "tool_used": final_output["tool_used"],
        "tool_result": final_output["tool_result"],
        "interaction_id": final_output["interaction_id"]
    }
