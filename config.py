import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

# Audio settings
SAMPLE_RATE = 16000
CHANNELS = 1
SILENCE_THRESHOLD = 500      # adjust if mic is too sensitive or not sensitive enough
SILENCE_DURATION = 2.0       # seconds of silence before we stop recording