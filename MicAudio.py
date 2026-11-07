# ! Wayland only, it won't translate to Windows
"""
Meaning I'm going to probably create an api to do this cross-platform or have to figure out pynput
"""
import time
import wave
import pyaudio
import threading

from evdev import InputDevice, categorize, ecodes

CHUNK = 1024

paused = False
running = True

# Initialize and to confirm
device = InputDevice("/dev/input/event3")

audio = pyaudio.PyAudio()
waveFile = wave.open("test_audio/Plastic_love.wav", "rb")

print(device)

OUTPUT_DEVICE_INDEX = 10
stream = audio.open(
        format=audio.get_format_from_width(waveFile.getsampwidth()),
        channels=waveFile.getnchannels(),
        rate=waveFile.getframerate(),
        output=True
    )

def input_listener():
    global paused, running
    try:
        for event in device.read_loop():
            # Check for key press (value == 1 means key down)
            if event.type == ecodes.EV_KEY and event.value == 1:
                if event.code == ecodes.KEY_SPACE:
                    paused = not paused
                    print(f"[Status] Paused: {paused}")
    except Exception:
        pass

# Create a separate thread to listen for inputs
listener_thread = threading.Thread(target=input_listener, daemon=True)
listener_thread.start()

if __name__ == "__main__":
    print("Playing... (Press Ctrl+C to exit)")

    try:
        data = waveFile.readframes(CHUNK)
        while data != b"" and running:
            if paused:
                time.sleep(0.1)
                continue

            stream.write(data)
            data = waveFile.readframes(CHUNK)

    except KeyboardInterrupt:
        pass

    # Cleanup
    running = False
    stream.stop_stream()
    stream.close()
    audio.terminate()
    waveFile.close()
