
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from ..db import get_session
from ..models import InterviewSession, QAItem, Message
from ..schemas import CreateSessionIn, SessionOut
from ..crew.prep_crew import run_prep

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/", response_model=SessionOut)
def create_session(body: CreateSessionIn, db: Session = Depends(get_session)):
    s = InterviewSession(
        role=body.role, 
        difficulty=body.difficulty,
        domain=body.domain, 
        job_description=body.job_description,
        status="preparing"
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    
    qas = run_prep(s.role, s.difficulty, s.domain, s.job_description)
    for i, qa in enumerate(qas):
        db.add(QAItem(
            session_id=s.id, 
            question=qa["question"], 
            ideal_answer=qa["ideal_answer"], 
            order_idx=i
        ))
    
    s.status = "ready"
    db.add(s)
    db.commit()
    
    return {"session_id": s.id, "status": s.status}

@router.get("/{session_id}/messages")
def get_session_messages(session_id: str, db: Session = Depends(get_session)):
    messages = db.exec(select(Message).where(Message.session_id == session_id).order_by(Message.ts)).all()
    return messages

@router.get("/{session_id}/questions")
def get_session_questions(session_id: str, db: Session = Depends(get_session)):
    questions = db.exec(select(QAItem).where(QAItem.session_id == session_id).order_by(QAItem.order_idx)).all()
    return questions