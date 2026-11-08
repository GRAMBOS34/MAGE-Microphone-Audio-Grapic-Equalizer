import include.MAGE as Audio

import include.input_handling as user_input

from evdev import InputDevice

keyboard_device = InputDevice("/dev/input/event3")
keyboard = user_input.Keyboard(keyboard_device)
keyboard.start_listener_thread()

audioEngine = Audio.MAGE(keyboard)

file = "test_audio/wav/Dracula.wav"

audioEngine.start_audio_playback(filepath=file)