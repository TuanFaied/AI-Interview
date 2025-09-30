from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlmodel import Session, select
from datetime import datetime, timedelta
import asyncio, json, logging

from .db import get_session
from .models import InterviewSession, QAItem, Message, Evaluation
from .services import storage, tts, evaluator, timeline
from .crew.interview_crew import InterviewBrain, INTRO_TEMPLATE

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/{session_id}")
async def interview_ws(ws: WebSocket, session_id: str, db: Session = Depends(get_session)):
    await ws.accept()
    logger.info(f"WebSocket connection opened for session {session_id}")

    s = db.get(InterviewSession, session_id)
    if not s or s.status not in ("ready", "live"):
        await ws.send_json(timeline.envelope("status", {"error": "invalid_or_not_ready"}))
        await ws.close()
        return

    qas = db.exec(
        select(QAItem).where(QAItem.session_id == session_id).order_by(QAItem.order_idx)
    ).all()

    qas_with_intro = [{"question": INTRO_TEMPLATE, "ideal_answer":(
    "A strong self-introduction should briefly cover:\n"
    "- Current role or academic background (e.g., 'I am a final year Computer Engineering undergraduate...').\n"
    "- Key skills or areas of expertise (e.g., software development, AI, databases).\n"
    "- Relevant experiences, internships, or projects.\n"
    "- Career interests and what they are looking for (e.g., seeking a software engineer role where I can apply...').\n\n"
    "The introduction should be clear, confident, and concise (about 30–60 seconds)."
    )}] + [
    {"question": q.question, "ideal_answer": q.ideal_answer} for q in qas
    ]
    brain = InterviewBrain(
        s.role, s.difficulty, s.domain,
        qas_with_intro
    )

    s.status = "live"
    s.started_at = datetime.utcnow()
    db.add(s)
    db.commit()

    deadline = s.started_at + timedelta(minutes=15)
    first_prompt = brain.next_prompt(None)
    await ws.send_json(timeline.envelope("interviewer_text", {"text": first_prompt}))
    audio_bytes = tts.synthesize(first_prompt)
    tts_url = storage.save_tts_bytes(audio_bytes)
    await ws.send_json(timeline.envelope("interviewer_audio", {"url": tts_url}))

    is_active = True
    current_question = first_prompt

    async def timer_task():
        nonlocal is_active
        while is_active:
            remain = int((deadline - datetime.utcnow()).total_seconds())
            if remain <= 0:
                await ws.send_json(timeline.envelope("status", {"message": "Interview completed"}))
                is_active = False
                break
            await ws.send_json(timeline.envelope("timer", {"remaining": remain}))
            await asyncio.sleep(1)

    timer = asyncio.create_task(timer_task())

    try:
        while is_active:
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=30.0)
                data = json.loads(msg)

                if data.get("type") == "candidate_text":
                    answer_text = data["data"]["text"]
                    logger.info(f"Candidate answered: {answer_text}")

                    db.add(Message(session_id=session_id, who="candidate", text=answer_text, ts=datetime.utcnow()))
                    db.commit()

                    await ws.send_json(
                        timeline.envelope("transcript", {"who": "candidate", "text": answer_text})
                    )
                    

                    next_prompt = brain.next_prompt(answer_text)
                    if next_prompt and next_prompt != current_question:
                        current_question = next_prompt
                        db.add(Message(session_id=session_id, who="interviewer", text=next_prompt, ts=datetime.utcnow()))
                        db.commit()
                        await ws.send_json(timeline.envelope("interviewer_text", {"text": next_prompt}))
                        audio_bytes = tts.synthesize(next_prompt)
                        tts_url = storage.save_tts_bytes(audio_bytes)
                        await ws.send_json(timeline.envelope("interviewer_audio", {"url": tts_url}))
                    else:
                        await ws.send_json(timeline.envelope("status", {"message": "Interview completed"}))
                        is_active = False

                elif data.get("type") == "control" and data["data"].get("action") == "stop":
                    await ws.send_json(timeline.envelope("status", {"message": "Interview completed"}))
                    is_active = False
                    break

            except asyncio.TimeoutError:
                continue

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    finally:
        is_active = False
        timer.cancel()
        try:
            s = db.get(InterviewSession, session_id)
            s.status = "finished"
            s.ended_at = datetime.now()
            db.add(s)
            db.commit()

            all_msgs = db.exec(
                select(Message).where(Message.session_id == session_id).order_by(Message.ts)
            ).all()
            transcript = "\n".join([f"{m.who.upper()}: {m.text}" for m in all_msgs])
            ev = evaluator.evaluate_transcript(session_id, s.role, s.difficulty, s.domain, db)
            db.add(
                Evaluation(
                    session_id=session_id,
                    technical=ev["technical"],
                    communication=ev.get("communication", 70),
                    confidence=ev["confidence"],
                    strengths=ev["strengths"],
                    summary=ev["summary"],
                    rubric_json=ev.get("rubric"),
                )
            )
            db.commit()
        except Exception as e:
            logger.error(f"Error during finalization: {e}")
        finally:
            await ws.close()
