import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    role = Column(String(50), default="field_rep")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    interactions = relationship("Interaction", back_populates="user")
    edits = relationship("InteractionEdit", back_populates="user")

class HCP(Base):
    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    specialty = Column(String(100))
    hospital_affiliation = Column(String(150))
    email = Column(String(150))
    phone = Column(String(30))
    preferred_channel = Column(String(30))  # call/visit/email
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp")

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    interaction_type = Column(String(30))  # visit/call/email/conference
    interaction_date = Column(DateTime, default=datetime.datetime.utcnow)
    channel = Column(String(30))
    topics_discussed = Column(JSON)  # Stores list of strings e.g. ["cardiology", "sales"]
    products_discussed = Column(JSON)  # Stores list of strings e.g. ["CardioShield"]
    sentiment = Column(String(20))  # positive/neutral/negative
    summary = Column(Text)
    raw_input = Column(Text)  # Original free text if conversational
    source = Column(String(20))  # 'form' or 'chat'
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date, nullable=True)
    samples_distributed = Column(JSON, nullable=True)  # dict e.g. {"product_name": quantity}
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")
    user = relationship("User", back_populates="interactions")
    edits = relationship("InteractionEdit", back_populates="interaction")

class InteractionEdit(Base):
    __tablename__ = "interaction_edits"

    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id"), nullable=False)
    edited_field = Column(String(60), nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    edited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    edited_at = Column(DateTime, default=datetime.datetime.utcnow)

    interaction = relationship("Interaction", back_populates="edits")
    user = relationship("User", back_populates="edits")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    thread_id = Column(String(80), unique=True, nullable=False, index=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
