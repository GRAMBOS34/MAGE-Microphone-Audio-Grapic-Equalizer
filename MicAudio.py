"""
Meaning I'm going to probably create an api to do this cross-platform or have to figure out pynput
"""
import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import threading

import include.input_handling as user_input

from evdev import InputDevice, categorize, ecodes # ! Wayland only, it won't translate to Windows nor Google Colab

paused = False
running = True

# Specifying the default device is necessary because
# otherwise, it would directly use the hardware itself
# and doing that doesn't play nice with Pipewire on Wayland
PULSE_DEVICE_INDEX = 18
sd.default.device = (None, PULSE_DEVICE_INDEX)

# Initialize the keyboard
keyboard_device = InputDevice("/dev/input/event3")
keyboard = user_input.Keyboard(keyboard_device)

class AudioFilePlayback():
    def __init__(self, filepath:str):
        self.keyboard = keyboard
        self.data, self.samplerate = sf.read(filepath)
        self.channels = self.data.shape[1] if len(self.data.shape) > 1 else 1

        # Create a separate thread to listen for inputs
        listener_thread = threading.Thread(target=keyboard.check_key_press, daemon=True)
        listener_thread.start()

    def play_audio(self):
        # * Gemini code but I'll over-explain
        # Open a stream to manually feed chunks
        with sd.OutputStream(samplerate=self.samplerate, channels=self.channels) as stream:
            """
                Basically, instead of writing the entire data array into
                the output stream, like in the use of the basic 'sd.play()'
                function, we only write a chunk of it at a time. The reason
                we want to do this is to give us the ability to pause and play
                the audio at any time.
            """

            blocksize = 1024
            block_start_idx = 0
            try:
                while running and block_start_idx < len(self.data):
                    # If paused, sleep briefly and skip writing audio chunks
                    if paused:
                        time.sleep(0.1)
                        continue
                    
                    # Write a chunk of audio
                    end_idx = min(block_start_idx + blocksize, len(self.data))
                    stream.write(np.float32(self.data[block_start_idx:end_idx]))
                    block_start_idx = end_idx
                    
            except KeyboardInterrupt:
                print("\nPlayback stopped.")