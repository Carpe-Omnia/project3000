import pyaudio
import numpy as np

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK = 1024
SILENCE_THRESHOLD = 200      # raise if it cuts off too early, lower if it never stops
SILENCE_DURATION = 2.0       # seconds of silence before we stop recording
FORMAT = pyaudio.paInt16


def record_until_silence() -> np.ndarray:
    audio = pyaudio.PyAudio()
    
    # Find the seeed device index
    device_index = None
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if 'seeed' in info['name'].lower():
            device_index = i
            print(f"[listen] Using device {i}: {info['name']}")
            break
    
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=CHUNK
    )

    print("[listen] Listening...")
    frames = []
    silent_chunks = 0
    required_silent_chunks = int(SILENCE_DURATION * SAMPLE_RATE / CHUNK)

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

        # Check volume level of this chunk
        audio_chunk = np.frombuffer(data, dtype=np.int16)
        volume = np.abs(audio_chunk).mean()
        
        print(f"[listen] volume: {volume:.1f}")  # ADD THIS LINE temporarily

        if volume < SILENCE_THRESHOLD:
            silent_chunks += 1
        else:
            silent_chunks = 0  # reset on any sound

        if silent_chunks >= required_silent_chunks and len(frames) > required_silent_chunks:
            break

    print("[listen] Done recording.")
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Convert to float32 for Whisper
    audio_data = np.frombuffer(b"".join(frames), dtype=np.int16)
    return audio_data.astype(np.float32) / 32768.0