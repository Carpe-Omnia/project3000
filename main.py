import menu
import time
import random
import glob
from pipeline.wake import wait_for_wake_word, flush_mic
from pipeline.listen import record_until_silence
from pipeline.transcribe import transcribe
from pipeline.think import get_response
from pipeline.speak import speak, play_file, play_file_async

SHUTOFF_KEYWORDS = [
    ["bye"],
    ["goodbye"],
    ["shut", "up"],
    ["that", "all"],
    ["go", "away"],
    ["enough"],
    ["stop"],
    ["done"],
    ["peace"],
    ["later"]
]

WAKE_FILES = sorted(glob.glob("audio/wake_responses/wake_*.wav"))
GOODBYE_FILES = sorted(glob.glob("audio/goodbye_responses/goodbye_*.wav"))
THINKING_FILES = sorted(glob.glob("audio/thinking_responses/thinking_*.wav"))


def get_wake_response():
    return random.choice(WAKE_FILES) if WAKE_FILES else None


def get_goodbye_response():
    return random.choice(GOODBYE_FILES) if GOODBYE_FILES else None

def get_thinking_response():
    return random.choice(THINKING_FILES) if THINKING_FILES else None

def is_shutoff(text: str) -> bool:
    words = text.lower().strip().split()
    for keyword_group in SHUTOFF_KEYWORDS:
        if all(any(kw in word for word in words) for kw in keyword_group):
            return True
    return False


def main():
    print("Starting Robomaz...")
    menu.start(blocking=True)

    print("Robomaz is ready.")
    speak("Hey, what's up. Ask me anything.")
    flush_mic(seconds=2.0)

    while True:
        try:
            # Stage 1: wait for wake word
            wait_for_wake_word()

            # Stage 2: acknowledge
            wake_file = get_wake_response()
            if wake_file:
                play_file(wake_file)
            else:
                speak("Yeah, what do you need?")
            flush_mic(seconds=1.5)

            # Stage 3: record customer
            audio = record_until_silence()

            # Stage 4: transcribe
            customer_message = transcribe(audio)
            print(f"[main] Customer said: '{customer_message}'")

            if not customer_message or len(customer_message.strip()) < 3:
                speak("Sorry, didn't catch that.")
                flush_mic(seconds=1.5)
                continue

            # Stage 5: check for shutoff
            if is_shutoff(customer_message):
                goodbye_file = get_goodbye_response()
                if goodbye_file:
                    play_file(goodbye_file)
                else:
                    speak("Later.")
                flush_mic(seconds=2.0)
                print("[main] Shutoff detected. Back to listening.")
                continue

            # Play thinking phrase WHILE Claude is being called
            # This runs instantly from disk, no API cost, makes the wait feel natural
            thinking_file = get_thinking_response()
            if thinking_file:
                play_file_async(thinking_file)

            # Stage 6: get response
            response = get_response(customer_message)

            # Stage 7: speak then flush
            speak(response)
            flush_mic(seconds=2.5)

        except KeyboardInterrupt:
            print("\nShutting down Robomaz.")
            goodbye_file = get_goodbye_response()
            if goodbye_file:
                play_file(goodbye_file)
            else:
                speak("Peace.")
            break
        except Exception as e:
            print(f"[main] Error: {e}")
            speak("Hold on, something went wrong on my end.")
            flush_mic(seconds=2.0)
            continue


if __name__ == "__main__":
    main()