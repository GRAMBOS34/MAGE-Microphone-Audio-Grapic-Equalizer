"""
Mic and keyboard handling
"""

import threading

from evdev import InputDevice, categorize, ecodes


class Keyboard:
    def __init__(self, device: InputDevice) -> None:
        self.device = device

        self.paused = False

    # TODO: Have it so that it can only poll for input when the window/console is in focus (?)
    def check_key_press(self) -> None:
        try:
            for event in self.device.read_loop():
                # Check for key press (value == 1 means key down)
                if event.type == ecodes.EV_KEY and event.value == 1:
                    if event.code == ecodes.KEY_SPACE:
                        self.paused = not self.paused
                        print(f"[Status] Paused: {self.paused}")

        except Exception:
            pass

    def start_listener_thread(self):
        # Create a separate thread to listen for inputs
        listener_thread = threading.Thread(target=self.check_key_press, daemon=True)
        listener_thread.start()
        print("Listener thread started")
