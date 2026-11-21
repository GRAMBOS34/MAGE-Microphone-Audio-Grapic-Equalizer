import customtkinter

from MAGE import MAGE, ui_frames

audioEngine = MAGE.AudioEngine() # Load audio engine

file = "test_audio/wav/ThankYouForTheVenom.wav"
audioEngine.load_audio(file)

customtkinter.set_appearance_mode("dark")  
customtkinter.set_default_color_theme("dark-blue")

# * ----------------- MAIN APP CLASS ------------------------
# I did it like this mainly because the docs say so but honestly, I see why
class MAGEApp(customtkinter.CTk):
    def __init__(self, audioEngine:MAGE.AudioEngine):
        super().__init__()
        self.audioEngine = audioEngine

        # * WINDOW INITIALIZATION
        self.title("MAGE - Microphone and Audio Graphic Equalizer")
        self.geometry("1500x600")
        self.resizable(False, False) # Keeps window fixed
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # * ON WINDOW CLOSE
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # * ----------------- WAVEFORM VISUALIZER ------------------------
        WAVE_BG_COLOR = "#FFFFFF"
        self.waveform_visualizer = ui_frames.WaveformVisualizer(
            self, 
            width=400, 
            height=250, 
            fg_color=WAVE_BG_COLOR, 
            audioEngine=audioEngine
        )
        self.waveform_visualizer.grid(row=0, column=0, padx=15, pady=15, sticky="nnw")

        # * ----------------- INPUT DEVICE SELECT ------------------------
        INPUT_SELECT_BG_COLOR = "#2b2b2b"
        self.input_device_select = ui_frames.InputDeviceSelect(
            self, 
            width=200, 
            height=275, 
            fg_color=INPUT_SELECT_BG_COLOR,
            audioEngine=audioEngine
        )
        self.input_device_select.grid(row=0, column=1, padx=15, pady=15, sticky="n")

        # * ----------------- GRAPHICAL EQUALIZER ------------------------
        GRAPHIC_EQ_BG_COLOR = "#2b2b2b"
        self.graphic_equalizer = ui_frames.GraphicEqualizer(
            self,
            width=640,
            height=315,
            fg_color=GRAPHIC_EQ_BG_COLOR,
            audioEngine=audioEngine
        )
        self.graphic_equalizer.grid(row=0, column=2, padx=15, pady=(15, 0), sticky="e")

        # * ----------------- OUTPUT DEVICE SELECT ------------------------
        OUTPUT_SELECT_BG_COLOR = "#00ff55"
        self.output_device_select = ui_frames.OutputDeviceSelect(
            self, 
            width=200, 
            height=275, 
            fg_color=OUTPUT_SELECT_BG_COLOR
        )
        self.output_device_select.grid(row=1, column=1, padx=15, pady=15, sticky="s")

        EFFECTS_PANELS_WIDTH = 600
        EFFECTS_PANELS_HEIGHT = 80
        # * ----------------- GAIN CONTROLS ------------------------
        GAIN_BG_COLOR = "#2b2b2b"
        self.gain_control = ui_frames.EffectsControls(
            self, 
            width=EFFECTS_PANELS_WIDTH, 
            height=EFFECTS_PANELS_HEIGHT, 
            fg_color=GAIN_BG_COLOR,
            audioEngine=audioEngine,
            effect="GAIN"
        )
        self.gain_control.grid(row=1, column=0, padx=15, pady=15, sticky="n")

        # * ----------------- HIGH-PASS FILTER CONTROLS ------------------------
        HPF_BG_COLOR = "#2b2b2b"
        self.HPF_control = ui_frames.EffectsControls(
            self, 
            width=EFFECTS_PANELS_WIDTH, 
            height=EFFECTS_PANELS_HEIGHT, 
            fg_color=HPF_BG_COLOR,
            audioEngine=audioEngine,
            effect="HPF"
        )
        self.HPF_control.grid(row=1, column=0, padx=15, pady=15, sticky="w")

        # * ----------------- LOW-PASS FILTER CONTROLS ------------------------
        LPF_BG_COLOR = "#2b2b2b"
        self.LPF_control = ui_frames.EffectsControls(
            self, 
            width=EFFECTS_PANELS_WIDTH, 
            height=EFFECTS_PANELS_HEIGHT, 
            fg_color=LPF_BG_COLOR,
            audioEngine=audioEngine,
            effect="LPF"
        )
        self.LPF_control.grid(row=1, column=0, padx=15, pady=15, sticky="s")

        # * ----------------- PLAYBACK CONTROLS ------------------------
        PLAYBACK_BG_COLOR = "#d900ff"
        self.playback_controls = ui_frames.PlaybackControls(
            self, 
            width=640, 
            height=275, 
            fg_color=PLAYBACK_BG_COLOR, 
            audioEngine=audioEngine
        )
        self.playback_controls.grid(row=1, column=2, padx=15, pady=15, sticky="sse")

    def on_closing(self):
        """
            Pauses the audio stream before closing the window.
            This is to avoid segfaulting every time the window
            is closed while audio is playing.
        """
        audioEngine.stop_engine()
        self.waveform_visualizer.stop_loop() # Stop calculating the waveform before closing

        self.destroy() # Close the window

if __name__ == "__main__":
    app = MAGEApp(audioEngine)
    app.mainloop()
