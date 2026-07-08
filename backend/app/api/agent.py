from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from db.session import get_db
import db.models as models
import schemas
from agent.graph import run_agent, agent_graph

router = APIRouter(prefix="/agent", tags=["AI Agent"])

@router.post("/chat", response_model=schemas.ChatResponse)
def chat_with_agent(chat_req: schemas.ChatRequest, db: Session = Depends(get_db)):
    # 1. Register or get session in db
    session = db.query(models.ChatSession).filter(models.ChatSession.thread_id == chat_req.thread_id).first()
    if not session:
        session = models.ChatSession(
            thread_id=chat_req.thread_id,
            user_id=chat_req.user_id,
            status="active"
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # 2. Run LangGraph agent
    try:
        result = run_agent(
            thread_id=chat_req.thread_id,
            user_id=chat_req.user_id,
            user_message=chat_req.message
        )
        return schemas.ChatResponse(
            reply=result["reply"],
            intent=result["intent"],
            tool_used=result["tool_used"],
            tool_result=result["tool_result"],
            interaction_id=result["interaction_id"]
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent runtime error: {str(e)}")

@router.get("/sessions/{thread_id}/history", response_model=schemas.SessionHistoryResponse)
def get_session_history(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    state = agent_graph.get_state(config)
    
    messages = []
    if state and state.values and "messages" in state.values:
        for msg in state.values["messages"]:
            # Format to schemas.ChatMessage
            role = msg.get("role")
            content = msg.get("content")
            if role and content:
                messages.append(schemas.ChatMessage(role=role, content=content))
                
    return schemas.SessionHistoryResponse(
        thread_id=thread_id,
        messages=messages
    )
