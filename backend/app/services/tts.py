import os
from google.cloud import texttospeech

def synthesize(text: str) -> bytes:
    json_path = os.path.join(os.path.dirname(__file__), "service_account.json")
    try:
        client = texttospeech.TextToSpeechClient.from_service_account_json(json_path)

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
            name="en-US-Chirp3-HD-Erinome"
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        return response.audio_content

    except Exception as e:
        # fallback: half a second of silence
        import numpy as np, soundfile as sf, io
        sr = 22050
        arr = np.zeros(int(sr * 0.5), dtype=np.float32)
        buff = io.BytesIO()
        sf.write(buff, arr, sr, format="WAV")
        print(f"Error in TTS synthesis: {e}")
        return buff.getvalue()





# import os
# from google.cloud import texttospeech

# def synthesize(text: str) -> bytes:
#     api_key = os.getenv("GOOGLE_API_KEY")
#     if not api_key:
#         # Fallback to silence if no Google Cloud credentials
#         import numpy as np, soundfile as sf, io
#         sr = 22050
#         arr = np.zeros(int(sr*0.5), dtype=np.float32)
#         buff = io.BytesIO()
#         sf.write(buff, arr, sr, format='WAV')
#         return buff.getvalue()

#     client = texttospeech.TextToSpeechClient()

#     synthesis_input = texttospeech.SynthesisInput(text=text)
#     voice = texttospeech.VoiceSelectionParams(
#         language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
#     )
#     audio_config = texttospeech.AudioConfig(
#         audio_encoding=texttospeech.AudioEncoding.MP3
#     )

#     response = client.synthesize_speech(
#         input=synthesis_input, voice=voice, audio_config=audio_config
#     )

#     return response.audio_content




# import os
# from openai import OpenAI

# def synthesize(text: str) -> bytes:
#     api_key = os.getenv("OPENAI_API_KEY")
#     if not api_key:
#         # Fallback to silence if no API key
#         import numpy as np, soundfile as sf, io
#         sr = 22050
#         arr = np.zeros(int(sr*0.5), dtype=np.float32)
#         buff = io.BytesIO()
#         sf.write(buff, arr, sr, format='WAV')
#         return buff.getvalue()
    
#     client = OpenAI(api_key=api_key)
#     response = client.audio.speech.create(
#         model="tts-1",
#         voice="alloy",
#         input=text,
#     )
#     return response.content