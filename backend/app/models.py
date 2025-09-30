from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
import uuid

class InterviewSession(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    role: str
    difficulty: str
    domain: Optional[str] = None
    job_description: Optional[str] = None
    status: str = Field(default="created")  # created|preparing|ready|live|finished|failed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    audio_path: Optional[str] = None

    qas: List["QAItem"] = Relationship(back_populates="session")
    scores: Optional["Evaluation"] = Relationship(back_populates="session")

class QAItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="interviewsession.id")
    question: str
    ideal_answer: str
    order_idx: int
    ts: datetime = Field(default_factory=datetime.utcnow)
    session: InterviewSession = Relationship(back_populates="qas")

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="interviewsession.id")
    who: str  
    text: str
    audio_path: Optional[str] = None  
    ts: datetime = Field(default_factory=datetime.utcnow)

class Evaluation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="interviewsession.id")
    technical: float
    strengths: str
    confidence: float
    communication: float
    summary: str
    rubric_json: Optional[str] = None

    session: InterviewSession = Relationship(back_populates="scores")