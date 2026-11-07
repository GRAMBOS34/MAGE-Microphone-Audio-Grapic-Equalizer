# ! Wayland only, it won't translate to Windows
"""
Meaning I'm going to probably create an api to do this cross-platform or have to figure out pynput
"""
import sounddevice as sd
import soundfile as sf

import threading

from evdev import InputDevice, categorize, ecodes

paused = False
running = True

# Initialize and to confirm
device = InputDevice("/dev/input/event3")

data, samplerate = sf.read('test_audio/Dracula.wav')

# This is necessary because it would just brick the audio interface since
# it would access the hardware directly through ALSA rather than through
# the Pipewire service. This also gives the bonus of being able to use the
# master volume of Pipewire to control volume.

PULSE_DEVICE_INDEX = 18
sd.default.device = (None, PULSE_DEVICE_INDEX)

sd.play(data, samplerate)

# Prevent the script from exiting early before the audio finishes
status = sd.wait()

def input_listener():
    global paused
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
