import httpx
import io
import subprocess
import numpy as np
import sounddevice as sd
import soundfile as sf
import threading
from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

CHUNK_SIZE = 4096  # bytes per streaming chunk


def speak(text: str):
    """Convert text to speech via ElevenLabs streaming and play it through speakers."""
    print("[speak] Generating speech (streaming)...")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"
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

    # Collect streamed MP3 chunks as they arrive
    mp3_buffer = io.BytesIO()
    with httpx.stream("POST", url, json=payload, headers=headers, timeout=30.0) as response:
        response.raise_for_status()
        for chunk in response.iter_bytes(chunk_size=CHUNK_SIZE):
            mp3_buffer.write(chunk)

    # Convert assembled MP3 to WAV and play
    mp3_buffer.seek(0)
    ffmpeg_proc = subprocess.run(
        ["ffmpeg", "-i", "pipe:0", "-f", "wav", "-ar", "22050", "-ac", "1", "pipe:1"],
        input=mp3_buffer.read(),
        capture_output=True
    )

    audio_data, sample_rate = sf.read(io.BytesIO(ffmpeg_proc.stdout))
    sd.play(audio_data, sample_rate)
    sd.wait()
    print("[speak] Done.")


def play_file(filepath: str):
    """Play a pre-generated audio file instantly, no API call."""
    audio_data, sample_rate = sf.read(filepath)
    sd.play(audio_data, sample_rate)
    sd.wait()


def play_file_async(filepath: str):
    """Play a pre-generated audio file in a background thread.
    Returns immediately while audio plays, so code keeps moving."""
    def _play():
        audio_data, sample_rate = sf.read(filepath)
        sd.play(audio_data, sample_rate)
        sd.wait()

    thread = threading.Thread(target=_play, daemon=True)
    thread.start()
    