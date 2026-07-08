from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import datetime

# HCP Schemas
class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    hospital_affiliation: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_channel: Optional[str] = "visit"
    notes: Optional[str] = None

class HCPCreate(HCPBase):
    pass

class HCPResponse(HCPBase):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Interaction Schemas
class InteractionBase(BaseModel):
    hcp_id: int
    interaction_type: str
    interaction_date: Optional[datetime.datetime] = None
    channel: Optional[str] = None
    topics_discussed: List[str] = []
    products_discussed: List[str] = []
    sentiment: Optional[str] = "neutral"
    summary: Optional[str] = None
    raw_input: Optional[str] = None
    source: str = "form"
    follow_up_required: bool = False
    follow_up_date: Optional[datetime.date] = None
    samples_distributed: Optional[Dict[str, int]] = None

class InteractionCreate(InteractionBase):
    pass

class InteractionUpdate(BaseModel):
    hcp_id: Optional[int] = None
    interaction_type: Optional[str] = None
    interaction_date: Optional[datetime.datetime] = None
    channel: Optional[str] = None
    topics_discussed: Optional[List[str]] = None
    products_discussed: Optional[List[str]] = None
    sentiment: Optional[str] = None
    summary: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime.date] = None
    samples_distributed: Optional[Dict[str, int]] = None

class InteractionResponse(InteractionBase):
    id: int
    user_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    hcp: Optional[HCPResponse] = None

    class Config:
        from_attributes = True

# Follow-up Schemas
class FollowUpResponse(BaseModel):
    id: int
    hcp_name: str
    specialty: Optional[str]
    interaction_id: int
    follow_up_date: datetime.date
    topics: List[str]
    products: List[str]

# Chat Schemas
class ChatRequest(BaseModel):
    thread_id: str
    user_id: int = 1
    message: str

class ChatResponse(BaseModel):
    reply: str
    intent: str
    tool_used: Optional[str] = None
    tool_result: Optional[Dict[str, Any]] = None
    interaction_id: Optional[int] = None

class ChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str

class SessionHistoryResponse(BaseModel):
    thread_id: str
    messages: List[ChatMessage]
