import whisper

# Load once at import time — keeps it fast during conversations
# Use "tiny" for speed, "small" for better accuracy
_model = whisper.load_model("tiny")


def transcribe(audio: "np.ndarray") -> str:
    """Takes float32 audio array, returns transcribed text string."""
    print("[transcribe] Transcribing...")
    result = _model.transcribe(audio, fp16=False, language="en")
    text = result["text"].strip()
    print(f"[transcribe] Heard: '{text}'")
    return text