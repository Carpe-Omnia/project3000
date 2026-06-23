import openai
import numpy as np
import soundfile as sf
import tempfile
import os
from config import OPENAI_API_KEY

_client = openai.OpenAI(api_key=OPENAI_API_KEY)


def transcribe(audio: np.ndarray) -> str:
    """Takes float32 audio array at 16000Hz, returns transcribed text."""
    print("[transcribe] Transcribing via OpenAI...")

    # Write to temp WAV file — OpenAI API needs a file not raw bytes
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, audio, 16000)
        tmppath = f.name

    try:
        with open(tmppath, "rb") as f:
            result = _client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="en",
                prompt="Cannabis dispensary customer asking about products, strains, edibles, vapes, or pre-rolls."
            )
        text = result.text.strip()
        print(f"[transcribe] Heard: '{text}'")
        return text
    finally:
        os.unlink(tmppath)