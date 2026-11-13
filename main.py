import tkinter as tk
from tkinter import ttk

import include.MAGE as Audio

audioEngine = Audio.MAGE() # Load audio engine

file = "test_audio/wav/FlyAway.wav"
audioEngine.load_audio(file)

# * WINDOW INITIALIZATION
WINDOW_DIMENSIONS = "1000x600"
root = tk.Tk()
root.geometry(WINDOW_DIMENSIONS)
root.resizable(False, False) # Keeps window fixed
root.title("MAGE - Microphone and Audio Graphic Equalizer")

# * PLAY BUTTON
play = tk.Button(root, text="Play Audio", padx=10, pady=5, command=audioEngine.toggle_play_pause)
play.place(relx=0.5, rely=0.5, anchor="center")

# * VOLUME SLIDER 
# ? It doesn't update in real-time though
volume_slider = tk.Scale(
    root, 
    from_=100, 
    to=0, 
    orient="vertical",
    command=audioEngine.change_volume,
    length=250
)
volume_slider.place(x=50, y=100)

volume_slider.set(50)

root.bind("<space>", lambda event: play.invoke()) # Play Button Keybind
root.mainloop()