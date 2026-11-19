import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

from MAGE import MAGE

# * Playback controls frame
class PlaybackControls(ctk.CTkFrame):
    def __init__(self, master, width, height, fg_color, audioEngine:MAGE.AudioEngine):
        super().__init__(master, width, height, fg_color=fg_color)
        self.audioEngine = audioEngine

        # * PLAY BUTTON
        self.playBtn = ctk.CTkButton(self, text="Play", command=self.toggle_play)
        self.playBtn.place(relx=0.5, rely=0.5, anchor="e")

        # * VOLUME SLIDER
        self.volumeSlider = ctk.CTkSlider(
            self,
            from_=0, 
            to=100, 
            orientation="vertical",
            command=audioEngine.change_volume
        )
        self.volumeSlider.place(relx=0.79, rely=0)

    def toggle_play(self):
        """
            Toggle play/pause and change the text of the button
        """
        self.audioEngine.toggle_play_pause()

        if self.audioEngine.paused:
            self.playBtn.configure(text="Play")

        else:
            self.playBtn.configure(text="Pause")

# * Waveform Visualizer Class
# ! AI was used for the embedding of matplotlib into a frame
# ! and the drawing of the grauh
class WaveformVisualizer(ctk.CTkFrame):
    def __init__(self, master, width, height, fg_color, audioEngine:MAGE.AudioEngine):
        super().__init__(master, width, height, fg_color=fg_color)
        self.audioEngine = audioEngine

        # Create a Matplotlib Figure and Axes
        self.fig = Figure(figsize=(5, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # Match dark mode aesthetic
        self.fig.patch.set_facecolor("#2b2b2b")
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0) # to fill the entire space

        self.ax.set_facecolor("#1e1e1e")
        self.ax.set_xscale("log") # set to a log scale
        self.ax.tick_params(labelbottom=False, labelleft=False, bottom=False, left=False) # hide tick values
        for spine in self.ax.spines.values():
            spine.set_color("#555555")

        # Initial plot data (e.g., dummy waveform or EQ curve)
        x = np.linspace(0, 20000, 1024)
        (self.line,) = self.ax.plot(x, np.sin(x), color="#3b8ed0")

        # 3. Embed the figure into the CTk frame
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=0, pady=0)

        self._phase = 0.0
        self._after_id = None
        self._update_graph()

    def _update_graph(self):
        data_block = self.audioEngine.data_block
        samplerate = self.audioEngine.samplerate

        if isinstance(data_block, np.ndarray) and isinstance(samplerate, int):
            mono_data_block = data_block.mean(axis=1) if data_block.ndim > 1 else data_block
            mono_data_block = np.asarray(mono_data_block, dtype=np.float32)

            # This uses a discrete fourier transform to get the frequencies we need 
            # and graphs it
            n = len(mono_data_block)
            window = np.hanning(n)
            freqs = np.fft.rfftfreq(len(mono_data_block), d=1.0/float(samplerate))
            self.mag = np.abs(np.fft.rfft(mono_data_block * window)) / (n / 2.0)

            # Defiine the decibel
            db = 20.0 * np.log10(np.maximum(self.mag, 1e-4))
            db = np.clip(db, -80.0, 0.0)

            # Fix the spectral tilt
            f_plot = np.geomspace(20.0, min(16000, samplerate/2), 256) # Put everything on a log scale
            y_plot = np.interp(f_plot, freqs, db)

            tilt_db_per_octave = 3.5
            pivot_hz = 1000.0

            octaves = np.log2(np.maximum(f_plot, 1.0) / pivot_hz)
            y_tilted = np.clip(y_plot + tilt_db_per_octave * octaves, -80.0, 0.0)

            # Removes noise
            # Basically ensures the line is flat throughout
            noise_floor_mask = y_plot <= -80.0
            y_plot = np.clip(y_tilted, -80.0, 0.0)
            y_plot[noise_floor_mask] = -80.0

            # Smooth across frames so it doesn't jitter
            if not hasattr(self, "_prev_y") or self._prev_y is None or len(self._prev_y) != len(y_plot):
                self._prev_y = y_plot
            else:
                self._prev_y = 0.65 * self._prev_y + 0.35 * y_plot
                    
            self.line.set_data(f_plot, self._prev_y)
            self.ax.set_ylim(-80.0, -10.0) # Changes how we view the graph
            self.canvas.draw_idle()

        self._after_id = self.after(50, self._update_graph)
        
    def stop_loop(self):
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None

# * Device Select Class (for input and output)
class DeviceSelect(ctk.CTkFrame):
    def __init__(self, master, width, height, fg_color):
        super().__init__(master, width, height, fg_color=fg_color)

# * Effects Controls Class
class EffectsControls(ctk.CTkFrame):
    def __init__(self, master, width, height, fg_color, audioEngine:MAGE.AudioEngine, effect:str):
        super().__init__(master, width, height, fg_color=fg_color)
        self.audioEngine = audioEngine
        self.effect = effect

        # * TOGGLE ENABLE BUTTON
        self.toggle_enable_btn = ctk.CTkButton(self, text="Enable", command=self.toggle_enable)
        self.toggle_enable_btn.place(relx=0.5, rely=0.5, anchor="e")

    def toggle_enable(self):
        """
            Toggle the effect and change the text of the button
        """
        self.audioEngine.toggle_enable_effect

        is_enabled = self.audioEngine.effects_chain[self.effect]["enabled"]
        print(f"{self.effect} {is_enabled}")

        if is_enabled:
            self.toggle_enable_btn.configure(text="Enable")

        else:
            self.toggle_enable_btn.configure(text="Disable")

        self.audioEngine.effects_chain[self.effect]["enabled"] = not is_enabled


