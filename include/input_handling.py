"""
Mic and keyboard handling
"""

from evdev import InputDevice, categorize, ecodes

class Keyboard:
    def __init__(self, device:InputDevice) -> None:
        self.device = device

    def check_key_press(self) -> None:
        global paused
        try:
            for event in self.device.read_loop():
                # Check for key press (value == 1 means key down)
                if event.type == ecodes.EV_KEY and event.value == 1:
                    if event.code == ecodes.KEY_SPACE:
                        paused = not paused
                        print(f"[Status] Paused: {paused}")

        except Exception:
            pass