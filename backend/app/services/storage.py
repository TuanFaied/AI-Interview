from pathlib import Path
import os, uuid
from datetime import datetime

BASE = Path(os.getenv("DATA_DIR", "./data"))
AUDIO_DIR = BASE/"audio"
TTS_DIR = BASE/"tts"
TRANSCRIPTS_DIR = BASE/"transcripts"

for d in [AUDIO_DIR, TTS_DIR, TRANSCRIPTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def session_audio_path(session_id: str) -> Path:
    return AUDIO_DIR / f"{session_id}"

def save_audio_chunk(session_id: str, audio_data: bytes) -> str:
    # Create session directory if it doesn't exist
    session_dir = AUDIO_DIR / session_id
    session_dir.mkdir(exist_ok=True)
    
    # Save audio chunk with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"chunk_{timestamp}.pcm"
    filepath = session_dir / filename
    
    with open(filepath, "wb") as f:
        f.write(audio_data)
    
    return str(filepath)

def save_transcript(session_id: str, transcript: str) -> str:
    # Create session directory if it doesn't exist
    session_dir = TRANSCRIPTS_DIR / session_id
    session_dir.mkdir(exist_ok=True)
    
    # Save transcript with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"transcript_{timestamp}.txt"
    filepath = session_dir / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(transcript)
    
    return str(filepath)

def save_tts_bytes(b: bytes) -> str:
    fid = f"{uuid.uuid4()}.mp3"
    p = TTS_DIR / fid
    p.write_bytes(b)
    return f"/static/tts/{fid}"