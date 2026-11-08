"""
Mic and keyboard handling
"""

from evdev import InputDevice, categorize, ecodes
import threading

class Keyboard:
    def __init__(self, device:InputDevice) -> None:
        self.device = device

        self.paused = False
        self.running = True

    def check_key_press(self) -> None:
        print("Debug")
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