from pydantic import BaseModel
from typing import List, Optional

class CreateSessionIn(BaseModel):
    role: str
    difficulty: str
    domain: Optional[str] = None
    job_description: Optional[str] = None

class SessionOut(BaseModel):
    session_id: str
    status: str

class QAOut(BaseModel):
    question: str
    ideal_answer: str
    order_idx: int

class EvaluationOut(BaseModel):
    technical: float
    strengths: str
    confidence: float
    communication: float
    summary: str

class StartInterviewOut(BaseModel):
    ok: bool
    ws_url: str