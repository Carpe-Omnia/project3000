import pyaudio
import numpy as np
import scipy.signal

SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK = 1024
SILENCE_THRESHOLD = 1500     # tuned for USB lavalier mic
SILENCE_DURATION = 2.0       # seconds of silence before we stop recording
FORMAT = pyaudio.paInt16


def record_until_silence() -> np.ndarray:
    """
    Records from mic until the speaker goes silent for SILENCE_DURATION seconds.
    Returns audio as a numpy float32 array ready for Whisper.
    """
    audio = pyaudio.PyAudio()

    # Find USB mic automatically
    device_index = None
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if 'usb' in info['name'].lower():
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

    # Discard first second — hardware warmup noise
    warmup_chunks = int(SAMPLE_RATE / CHUNK * 1.0)
    print("[listen] Warming up mic...")
    for _ in range(warmup_chunks):
        stream.read(CHUNK, exception_on_overflow=False)

    print("[listen] Listening...")
    frames = []
    silent_chunks = 0
    peak_volume = 0
    has_speech = False
    required_silent_chunks = int(SILENCE_DURATION * SAMPLE_RATE / CHUNK)

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

        # RMS volume — always positive, handles signed int16 correctly
        audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32)
        volume = np.sqrt(np.mean(audio_chunk**2))

        # Track peak to detect relative silence
        if volume > peak_volume:
            peak_volume = volume

        # Dynamic threshold — silence is when volume drops to 20% of peak
        dynamic_threshold = max(SILENCE_THRESHOLD, peak_volume * 0.2)

        if volume < dynamic_threshold:
            silent_chunks += 1
        else:
            silent_chunks = 0
            if volume > SILENCE_THRESHOLD * 2:
                has_speech = True  # confirm we actually heard something

        # Only stop if we detected speech AND then silence
        if has_speech and silent_chunks >= required_silent_chunks:
            break

        # Safety timeout — 15 seconds max
        if len(frames) > SAMPLE_RATE / CHUNK * 15:
            print("[listen] Timeout reached.")
            break

    print("[listen] Done recording.")
    stream.stop_stream()
    stream.close()
    audio.terminate()

    audio_data = np.frombuffer(b"".join(frames), dtype=np.int16).astype(np.float32) / 32768.0

    # Resample from 44100 to 16000 for Whisper
    import scipy.signal
    audio_resampled = scipy.signal.resample_poly(audio_data, 16000, 44100)

    return audio_resampled