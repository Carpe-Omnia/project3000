import httpx
import io
import subprocess
import numpy as np
import sounddevice as sd
import soundfile as sf
from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID


def speak(text: str):
    """Convert text to speech via ElevenLabs and play it through speakers."""
    print("[speak] Generating speech...")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
    response.raise_for_status()

    # Use ffmpeg to convert MP3 bytes to WAV bytes in memory
    ffmpeg_proc = subprocess.run(
        ["ffmpeg", "-i", "pipe:0", "-f", "wav", "-ar", "22050", "-ac", "1", "pipe:1"],
        input=response.content,
        capture_output=True
    )

    # Read WAV from memory and play
    audio_data, sample_rate = sf.read(io.BytesIO(ffmpeg_proc.stdout))
    sd.play(audio_data, sample_rate)
    sd.wait()
    print("[speak] Done.")