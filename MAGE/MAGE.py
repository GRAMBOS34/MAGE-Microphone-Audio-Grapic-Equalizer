import platform
import time
import threading

import numpy as np
import sounddevice as sd
import soundfile as sf

import MAGE.effects as effects

class AudioEngine:
    def __init__(self):
        self.running = False
        self.paused = False

        # Audio Data
        self.file_data = None
        self.samplerate = None
        self.channels = None
        self.volume = 0.5
        self.effects_chain = effects.load_effects() # loads effects before playback

        # For the waveform visualizer
        self.data_block = None

        # This may have been unique to my system but it didn't
        # default to PipeWire but instead ALSA
        if platform.system() == "Linux":
            # ! For Linux only
            # (Input, Output)
            sd.default.device = (None, "pipewire")

    def toggle_enable_effect(self, effect_name:str) -> None:
        is_enabled = self.effects_chain[effect_name]["enabled"]

        self.effects_chain[effect_name]["enabled"] = not is_enabled

    def stop_engine(self):
        """
            Stop everything in order to avoid segfaulting
        """
        self.paused = True
        self.running = False

        time.sleep(0.05) # To really avoid segfaulting
    
    def load_audio(self, filepath: str):
        """
            Checks if file type is supported before loading and throws an error
            if it is not supported

            Different filetypes are automatically handled by soundfile

            Args:
            filepath: str
        """
        
        self.file_data, self.samplerate = sf.read(filepath)
        self.channels = self.file_data.shape[1] if len(self.file_data.shape) > 1 else 1
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

        print(f"Paused: {self.paused}")

    def audio_playback(self):
        if self.file_data is None:
            print("Data not loaded")
            return

        if not isinstance(self.samplerate, int):
            print("Failed reading audio data")
            return

        with sd.Stream(samplerate=self.samplerate, channels=self.channels) as stream:
            # TODO: figure out seeking
            # TODO: show where in the file it currently is

            blocksize = 1024
            block_start_idx = 0

            print("Playing audio...")
            try: 
                previous_zi_state = None

                while self.running == True and block_start_idx < len(self.file_data):
                    # If paused, sleep briefly and skip writing audio chunks
                    if self.paused:
                        time.sleep(0.1)
                        continue

                    # Write a chunk of audio
                    end_idx = min(block_start_idx + blocksize, len(self.file_data))

                    # Had to convert to float32 since stream.write doesnt use float64
                    pre_effect_data_block = np.float32(self.file_data[block_start_idx:end_idx])

                    # * Appply effects
                    self.data_block, zi_state = effects.process_effects(pre_effect_data_block, self.samplerate, self.effects_chain, previous_zi_state)

                    self.data_block = np.float32(self.data_block) * self.volume
                    
                    stream.write(self.data_block) 
                    
                    block_start_idx = end_idx  # switch index to the next chunk
                    previous_zi_state = zi_state

            finally:
                self.running = False
                print("\nPlayback stopped.")
