import pyaudio
import numpy as np

SAMPLE_RATE = 16000
CHANNELS = 2  # change from 1 to 2
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
        audio_chunk = np.frombuffer(data, dtype=np.int16).reshape(-1, 2)
        audio_chunk = audio_chunk[:, 0].astype(np.float32)  # left channel only
        volume = np.sqrt(np.mean(audio_chunk**2))
        
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

    # Reshape to stereo and take left channel only
    stereo = audio_data.reshape(-1, 2)
    mono = stereo[:, 0]  # left channel — the one facing you
    
    return mono.astype(np.float32) / 32768.0