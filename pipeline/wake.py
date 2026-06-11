import pyaudio
import numpy as np
import time
from openwakeword.model import Model

_model = Model(wakeword_models=["models/hey_robomaz.onnx"], inference_framework="onnx")

CHUNK = 1280
SAMPLE_RATE = 16000
FORMAT = pyaudio.paInt16
CHANNELS = 1
ACTIVATION_THRESHOLD = 0.7  # raised from 0.5 — less trigger-happy


def flush_mic(seconds=2.0):
    """
    Reads and discards audio from the mic for a given duration.
    Call this after Robomaz finishes speaking to clear out any
    residual speaker output before we start listening for wake word.
    """
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    chunks_to_discard = int((seconds * SAMPLE_RATE) / CHUNK)
    print(f"[wake] Flushing mic for {seconds}s...")
    
    for _ in range(chunks_to_discard):
        stream.read(CHUNK, exception_on_overflow=False)
    
    # Also reset the model's internal state so scores start fresh
    _model.reset()
    
    stream.stop_stream()
    stream.close()
    audio.terminate()


def wait_for_wake_word():
    """
    Listens continuously until the wake word is detected.
    Blocks until activation, then returns.
    """
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    print("[wake] Listening for wake word ('hey robomaz')...")

    # Require N consecutive chunks above threshold before triggering
    # prevents a single loud noise from setting him off
    consecutive_required = 3
    consecutive_count = 0

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        audio_chunk = np.frombuffer(data, dtype=np.int16)
        prediction = _model.predict(audio_chunk)

        for model_name, score in prediction.items():
            if score > ACTIVATION_THRESHOLD:
                consecutive_count += 1
                if consecutive_count >= consecutive_required:
                    print(f"[wake] Wake word detected! (score: {score:.2f})")
                    stream.stop_stream()
                    stream.close()
                    audio.terminate()
                    return
            else:
                consecutive_count = 0  # reset on any weak chunk