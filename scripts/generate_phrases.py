import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import subprocess
from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

WAKE_RESPONSES = [
    "Yo, sup?",
    "sup brah?",
    "What's good?",
    "Talk to me.",
    "How you living?",
]

GOODBYE_RESPONSES = [
    "Later brah.",
    "Aight, peace.",
    "Come back anytime.",
    "Stay up.",
    "I'm here all day.",
]

OUTPUT_DIR_WAKE = "audio/wake_responses"
OUTPUT_DIR_GOODBYE = "audio/goodbye_responses"


def generate_phrase(text: str, output_path: str):
    """Generate a single phrase and save it to output_path."""
    print(f"Generating: '{text}'")
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

    ffmpeg_proc = subprocess.run(
        ["ffmpeg", "-i", "pipe:0", "-f", "wav", "-ar", "22050", "-ac", "1", "pipe:1"],
        input=response.content,
        capture_output=True
    )

    with open(output_path, "wb") as f:
        f.write(ffmpeg_proc.stdout)
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR_WAKE, exist_ok=True)
    os.makedirs(OUTPUT_DIR_GOODBYE, exist_ok=True)

    for i, phrase in enumerate(WAKE_RESPONSES):
        generate_phrase(phrase, os.path.join(OUTPUT_DIR_WAKE, f"wake_{i}.wav"))

    for i, phrase in enumerate(GOODBYE_RESPONSES):
        generate_phrase(phrase, os.path.join(OUTPUT_DIR_GOODBYE, f"goodbye_{i}.wav"))

    print(f"\nDone. Generated {len(WAKE_RESPONSES) + len(GOODBYE_RESPONSES)} phrases.")