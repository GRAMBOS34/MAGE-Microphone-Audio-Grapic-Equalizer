import threading
import tkinter as tk
from tkinter import ttk

import include.MAGE as Audio

audioEngine = Audio.MAGE()

file = "test_audio/wav/FlyAway.wav"
audioEngine.load_audio(file)

WINDOW_DIMENSIONS = "1000x600"

root = tk.Tk()
root.geometry(WINDOW_DIMENSIONS)
root.title("MAGE - Microphone and Audio Graphic Equalizer")

# Create and center the button
button = tk.Button(root, text="Play Audio", padx=10, pady=5, command=audioEngine.audio_playback)
button.place(relx=0.5, rely=0.5, anchor="center")

root.mainloop()