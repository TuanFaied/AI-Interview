from faster_whisper import WhisperModel
import os, io, wave, logging
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_model = None

def get_model():
    global _model
    if _model is None:
        size = os.getenv("ASR_MODEL", "small")
        _model = WhisperModel(size, device="cpu", compute_type="int8")
    return _model


def transcribe_chunk(pcm_bytes: bytes, sample_rate: int = 16000) -> str:
    """
    Transcribe raw PCM16 audio (wrap into WAV in-memory).
    """
    if len(pcm_bytes) < 8000:  # ~0.5s @16kHz
        logger.info(f"Skipping tiny buffer: {len(pcm_bytes)} bytes")
        return ""

    # Wrap PCM into an in-memory WAV
    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)

    wav_io.seek(0)

    try:
        # Use VAD filter to detect speech segments
        segments, _ = get_model().transcribe(
            wav_io, 
            vad_filter=True, 
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200,
            ),
            language="en"
        )

        texts = []
        for seg in segments:
            if seg.text.strip():
                texts.append(seg.text.strip())

        result = " ".join(texts).strip()
        logger.info(f"Transcribed: '{result}'")
        return result
    except Exception as e:
        logger.error(f"ASR Error: {e}")
        return ""