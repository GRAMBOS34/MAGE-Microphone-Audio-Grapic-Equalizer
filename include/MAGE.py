"""
This file is meant to run on Linux, particularly with a Wayland server.

That's why I didn't use a library like pynput. 

Although using pynput is the plan in the future.

Well it's honestly either I switch the whole thing to pynput or make
an entire input library built to handle either pynput or evdev
"""
import sounddevice as sd
import soundfile as sf
import numpy as np
import time

import include.input_handling as user_input
import include.effects as effects

from evdev import InputDevice # ! Wayland only, it won't translate to Windows nor Google Colab (that's not the plan anyway)

# Specifying the default device is necessary because
# otherwise, it would directly use the hardware itself
# and doing that doesn't play nice with Pipewire on Wayland
PULSE_DEVICE_INDEX = 18
sd.default.device = (None, PULSE_DEVICE_INDEX)

# ! THIS IS A WAYLAND IMPLEMENTATION
# ! THIS IS NOT COMPATIBLE WITH WINDOWS OR X11
# Initialize the keyboard
keyboard_device = InputDevice("/dev/input/event3")
keyboard = user_input.Keyboard(keyboard_device)

class MAGE:
    # TODO: Make the keyboard interface optional
    # I don't know how to set this to "None" to be honest
    def __init__(self, keyboard=keyboard):
        self.keyboard = keyboard
        self.running = True

    def start_audio_playback(self, filepath:str, paused=False):
        data, samplerate = sf.read(filepath)

        # Check if it's mono or stereo
        channels = data.shape[1] if len(data.shape) > 1 else 1

        info = sf.info(filepath) # ? For metadata and showing a progress indicator (not yet implemented)

        with sd.OutputStream(samplerate=samplerate, channels=channels) as stream:
           
            # TODO: figure out seeking
            # TODO: show where in the file it currently is

            blocksize = 1024
            block_start_idx = 0
            try:
                print("Playing audio...")
                while self.running == True and block_start_idx < len(data):
                    paused = self.keyboard.paused # check every loop

                    # If paused, sleep briefly and skip writing audio chunks
                    if paused:
                        time.sleep(0.1)
                        continue
                    
                    # Write a chunk of audio
                    end_idx = min(block_start_idx + blocksize, len(data))

                    # Had to convert to float32 since stream.write doesnt use float64
                    pre_effect_data_block = np.float32(data[block_start_idx:end_idx])

                    # TODO: make it so that applying effects is actually on a different function
                    # like it can be added or removed pretty easily
                    data_block = effects.high_pass_filter(pre_effect_data_block, samplerate, 400)

                    # ! Comment one out
                    # stream.write(np.float32(data_block)) # HPF Applied
                    stream.write(pre_effect_data_block) # No effect applied

                    block_start_idx = end_idx
                    
            except KeyboardInterrupt: # Ctrl + C on the console
                self.running = False

            print("\nPlayback stopped.")