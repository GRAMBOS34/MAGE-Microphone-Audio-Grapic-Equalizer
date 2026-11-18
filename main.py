from typing import Tuple

import customtkinter
from tkinter import ttk

from MAGE import MAGE

audioEngine = MAGE.AudioEngine() # Load audio engine

file = "test_audio/wav/PlasticLove.wav"
audioEngine.load_audio(file)

customtkinter.set_appearance_mode("system")  
customtkinter.set_default_color_theme("dark-blue")

class PlaybackControls(customtkinter.CTkFrame):
    def __init__(self, master, width, height, fg_color):
        super().__init__(master, width, height, fg_color=fg_color)

        # * PLAY BUTTON
        button_text = "Play"
        if not audioEngine.paused:
            button_text = "Pause"

        self.playBtn = customtkinter.CTkButton(self, text="Play", command=self.toggle_play)
        self.playBtn.place(relx=0.5, rely=0.5, anchor="e")

        # * VOLUME SLIDER
        self.volumeSlider = customtkinter.CTkSlider(
            self,
            from_=0, 
            to=100, 
            orientation="vertical",
            command=audioEngine.change_volume
        )
        self.volumeSlider.place(relx=0.79, rely=0)

    def on_space_pressed(self, event):
        self.toggle_play()

    def toggle_play(self):
        audioEngine.toggle_play_pause()

        if audioEngine.paused:
            self.playBtn.configure(text="Play")

        else:
            self.playBtn.configure(text="Pause")

class WaveformVisualizer(customtkinter.CTkFrame):
    def __init__(self, master, width, height, fg_color):
        super().__init__(master, width, height, fg_color=fg_color)

# Main App class
# I did it like this mainly because the docs say so but honestly, I see why
class MAGEApp(customtkinter.CTk):
    def __init__(self, audioEngine:MAGE.AudioEngine):
        super().__init__()
        self.audioEngine = audioEngine

        # * WINDOW INITIALIZATION
        self.title("MAGE - Microphone and Audio Graphic Equalizer")
        self.geometry("1000x600")
        self.resizable(False, False) # Keeps window fixed
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # * ON WINDOW CLOSE
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # * ----------------- PLAYBACK CONTROLS ------------------------
        PLAYBACK_BG_COLOR = "#7F7F7F"
        self.playback_controls = PlaybackControls(self, width=400, height=200, fg_color=PLAYBACK_BG_COLOR)
        self.playback_controls.grid(row=3, column=3, padx=15, pady=15, sticky="sse")

        # * ----------------- WAVEFORM VISUALIZER ------------------------
        WAVE_BG_COLOR = "#FFFFFF"
        self.waveform_visualizer = WaveformVisualizer(self, width=400, height=250, fg_color=WAVE_BG_COLOR)
        self.waveform_visualizer.grid(row=0, column=0, padx=15, pady=15, sticky="nnw")

    def on_closing(self):
        """
            Pauses the audio stream before closing the window.
            This is to avoid segfaulting every time the window
            is closed while audio is playing.
        """
        audioEngine.stop_engine()

        self.destroy()

if __name__ == "__main__":
    app = MAGEApp(audioEngine)
    app.mainloop()
