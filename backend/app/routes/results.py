from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from ..db import get_session
from ..models import Evaluation
from ..schemas import EvaluationOut

router = APIRouter(prefix="/results", tags=["results"])

@router.get("/{session_id}", response_model=EvaluationOut)
def get_results(session_id: str, db: Session = Depends(get_session)):
    ev = db.exec(select(Evaluation).where(Evaluation.session_id==session_id)).first()
    if not ev:
        return EvaluationOut(
            technical=0, 
            strengths="Pending", 
            confidence=0, 
            communication=0, 
            summary="Awaiting evaluation"
        )
    
    return EvaluationOut(
        technical=ev.technical, 
        strengths=ev.strengths, 
        confidence=ev.confidence, 
        communication=ev.communication, 
        summary=ev.summary
    )