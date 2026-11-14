import tkinter as tk
from tkinter import ttk

import include.MAGE as Audio

audioEngine = Audio.MAGE() # Load audio engine

file = "test_audio/wav/PlasticLove.wav"
audioEngine.load_audio(file)

# * WINDOW INITIALIZATION
WINDOW_DIMENSIONS = "1000x600"
root = tk.Tk()
root.geometry(WINDOW_DIMENSIONS)
root.resizable(False, False) # Keeps window fixed
root.title("MAGE - Microphone and Audio Graphic Equalizer")

# * ----------------- PLAYBACK CONTROLS ------------------------

PLAYBACK_BG_COLOR = "#55D2FF"
playback_controls = tk.Frame(root, bg=PLAYBACK_BG_COLOR, padx=15, pady=15, width=400, height=200)
playback_controls.pack(pady=20, padx=20, fill="none", side="bottom", anchor="e")

# * PLAY BUTTON
play = tk.Button(playback_controls, text="Play Audio", padx=10, pady=5, command=audioEngine.toggle_play_pause)
play.place(relx=0.5, rely=0.5, anchor="e")

# * VOLUME SLIDER 
# ? It doesn't update in real-time though
volume_slider = tk.Scale(
    playback_controls, 
    from_=100, 
    to=0, 
    orient="vertical",
    command=audioEngine.change_volume,
    length=150,

    background="#FFFFFF",

    # Remove Border
    bd=0, 
    highlightthickness=0,
    showvalue=False # Hides the value
)
volume_slider.place(relx=0.79, rely=0)
volume_slider.set(50) # Set default value to 50%

volume_label = tk.Label(playback_controls, text="Volume")
volume_label.place(relx=0.75, rely=0.90)

root.bind("<space>", lambda event: play.invoke()) # Play Button Keybind
root.mainloop()