from datetime import datetime

def envelope(kind: str, payload: dict):
    return {"type": kind, "ts": datetime.utcnow().isoformat(), "data": payload}