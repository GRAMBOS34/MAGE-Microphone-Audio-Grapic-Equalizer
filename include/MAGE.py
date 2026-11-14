import platform
import time
import threading

import numpy as np
import sounddevice as sd
import soundfile as sf

import include.effects as effects

SUPPORTED_FILE_TYPES = [".wav"] # TODO: figure out mp3 support

class MAGE:
    # TODO: Set a keyboard interface
    def __init__(self):
        self.running = False
        self.paused = False

        # Audio Data
        self.data = None
        self.samplerate = None
        self.channels = None
        self.volume = 0.5

        # This may have been unique to my system but it didn't
        # default to PipeWire but instead ALSA
        if platform.system() == "Linux":
            # ! For Linux only
            # (Input, Output)
            sd.default.device = (None, "pipewire")
    
    # TODO: add file type checking
    def load_audio(self, filepath: str):
        """
            Checks if file type is supported before loading

            Args:
            filepath: str
        """
        self.data, self.samplerate = sf.read(filepath)
        self.channels = self.data.shape[1] if len(self.data.shape) > 1 else 1
        info = sf.info(filepath)  # ? For metadata and showing a progress indicator (not yet implemented)

        print(f"{filepath} loaded")

    def change_volume(self, value):
        """
            Changes the volume (this is NOT preamp gain)

            Args:
            volume: str (because the slider outputs a string for some reason?)
        """

        self.volume = int(value) / 100

    def toggle_play_pause(self):
        """
            Toggle Play/Pause but if its the first time running, 
            it creates a thread for audio playback
        """

        if self.running == False:
            # Start the audio thread
            audio_thread = threading.Thread(target=self.audio_playback)
            audio_thread.daemon = True
            audio_thread.start()
            self.running = True

        else:
            self.paused = not self.paused

    def audio_playback(self):
        if self.data is None:
            print("Data not loaded")
            return

        with sd.OutputStream(samplerate=self.samplerate, channels=self.channels) as stream:
            # TODO: figure out seeking
            # TODO: show where in the file it currently is

            blocksize = 1024
            block_start_idx = 0
            try:
                print("Playing audio...")
                while self.running == True and block_start_idx < len(self.data):
                    # If paused, sleep briefly and skip writing audio chunks
                    if self.paused:
                        time.sleep(0.1)
                        continue

                    # Write a chunk of audio
                    end_idx = min(block_start_idx + blocksize, len(self.data))

                    # Had to convert to float32 since stream.write doesnt use float64
                    pre_effect_data_block = np.float32(self.data[block_start_idx:end_idx])

                    # TODO: make it so that applying effects is actually on a different function
                    # like it can be added or removed pretty easily
                    data_block = effects.high_pass_filter(pre_effect_data_block, self.samplerate, 400)

                    # ! Comment one out
                    # stream.write(np.float32(data_block)) # HPF Applied
                    stream.write(pre_effect_data_block * self.volume)  # No effect applied

                    block_start_idx = end_idx

            except KeyboardInterrupt:  # Ctrl + C on the console
                self.running = False

            print("\nPlayback stopped.")
