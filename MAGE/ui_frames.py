import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from typing import Callable, Union, Optional

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
# ! and the drawing of the graph
class WaveformVisualizer(ctk.CTkFrame):
    def __init__(self, master, width, height, fg_color, audioEngine:MAGE.AudioEngine):
        super().__init__(master, width, height, fg_color=fg_color)
        self.audioEngine = audioEngine

        # Create a Matplotlib Figure and Axes
        GRAPH_WIDTH = 7
        GRAPH_HEIGHT = 3
        self.fig = Figure(figsize=(GRAPH_WIDTH, GRAPH_HEIGHT), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # Match dark mode aesthetic
        self.fig.patch.set_facecolor("#2b2b2b")
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0) # to fill the entire space

        self.ax.set_facecolor("#1e1e1e")
        self.ax.set_xscale("log") # set x-axis to a log scale
        self.ax.tick_params(labelbottom=False, labelleft=False, bottom=False, left=False) # hide tick values
        for spine in self.ax.spines.values():
            spine.set_color("#555555")

        # Initial plot data (e.g., dummy waveform or EQ curve)
        x = np.linspace(0, 20000, 1024)
        (self.line,) = self.ax.plot(x, np.sin(x), color="#3b8ed0")

        # Embed the figure into the CTk frame
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=0, pady=0)

        # Continuously update the graph
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

    # Call as a destructor
    def stop_loop(self):
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None

# ? I took this from the spinbox example of the customtkinter docs
class FloatSpinbox(ctk.CTkFrame):
    def __init__(self, *args,
                 width: int = 100,
                 height: int = 32,
                 step_size: Union[int, float] = 1,
                 command: Optional[Callable] = None,
                 **kwargs):
        super().__init__(*args, width=width, height=height, **kwargs)

        self.step_size = step_size
        self.command = command

        self.configure(fg_color=("gray78", "gray28"))  # set frame color

        self.grid_columnconfigure((0, 2), weight=0)  # buttons don't expand
        self.grid_columnconfigure(1, weight=1)  # entry expands

        self.subtract_button = ctk.CTkButton(
            self, 
            text="-", 
            width=height-6,
            height=height-6, 
            command=self.subtract_button_callback
        )
        self.subtract_button.grid(row=0, column=0, padx=(3, 0), pady=3)

        vcmd = (self.register(self._validate_positive), "%P")
        self.entry = ctk.CTkEntry(
            self, 
            width=width-(2*height), 
            height=height-6, 
            border_width=0, 
            justify="center",
            validate="key",
            validatecommand=vcmd
        )
        self.entry.grid(row=0, column=1, columnspan=1, padx=3, pady=3, sticky="ew")

        self.add_button = ctk.CTkButton(
            self, 
            text="+", 
            width=height-6, 
            height=height-6, 
            command=self.add_button_callback
        )
        self.add_button.grid(row=0, column=2, padx=(0, 3), pady=3)

        # default value
        self.entry.insert(0, "0.0")

    def _validate_positive(self, proposed_value:str) -> bool:
        """
            Checks if the value is valid or not
        """
        if proposed_value in ("", "."):
            return True

        if proposed_value.startswith("-") or " " in proposed_value:
            return False

        try:
            value = float(proposed_value)
        except ValueError:
            return False

        return value > 0

    def add_button_callback(self):
        if self.command is not None:
            self.command()
        try:
            value = float(self.entry.get()) + self.step_size
            self.entry.delete(0, "end")
            self.entry.insert(0, value)
        except ValueError:
            return

    def subtract_button_callback(self):
        if self.command is not None:
            self.command()
        try:
            value = float(self.entry.get()) - self.step_size
            self.entry.delete(0, "end")
            self.entry.insert(0, value)
        except ValueError:
            return

    def get(self) -> Union[float, None]:
        try:
            return float(self.entry.get())
        except ValueError:
            return None

    def set(self, value: float):
        self.entry.delete(0, "end")
        self.entry.insert(0, str(float(value)))

class EQSlider(ctk.CTkFrame):
    def __init__(self, master, channel:list[float], height, audioEngine:MAGE.AudioEngine, index, width=40):
        super().__init__(master, width, height, corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_propagate(False) # Keep size fixed
        self.index = index

        FREQ_INDEX = 0
        GAIN_INDEX = 1
        Q_INDEX = 2

        self.audioEngine = audioEngine
        self.affected_freq = channel[FREQ_INDEX]
        self.gain = channel[GAIN_INDEX]
        self.Q_val = channel[Q_INDEX]

        self.gain_slider = ctk.CTkSlider(
            self,
            width=20,
            from_=-50, 
            to=20,
            command=self.adjust_gain,
            orientation="vertical",
        )
        self.gain_slider.grid(row=0, column=0, padx=0, pady=5, sticky="n")

        """
            Ideally self.affected_freq and self.q_setting would be using CTkEntry
            so that these can be modified during runtime, but I didn't have time to 
            do that so for now this is how it is
        """
        self.affected_freq = ctk.CTkLabel(
            self,
            text_color="#FFFFFF", 
            width=40, 
            text=self._format_freq(self.affected_freq),
            font=("JetBrains Mono", 12) # (font, font size)
        )
        self.affected_freq.grid(row=1, column=0, padx=0, pady=10, sticky="n")

        self.q_setting = ctk.CTkLabel(
            self,
            text_color="#FFFFFF", 
            width=40, 
            text=str(self.Q_val),
            font=("JetBrains Mono", 12) # (font, font size)
        )
        self.q_setting.grid(row=2, column=0, padx=0, pady=5, sticky="n")

    def adjust_gain(self, gain_value:float):
        self.audioEngine.effects_chain["GEQ"]["properties"][self.index][1] = gain_value

    def _format_freq(self, value: float) -> str:
        if value >= 1000:
            k_val = value / 1000
            # Drop ".0" for whole thousands like 10000 -> "10k", keep decimals like 1250 -> "1.25k"
            formatted = f"{k_val:g}"
            return f"{formatted}k"
        return f"{value:g}"

# * Graphic Equalizer Class
class GraphicEqualizer(ctk.CTkFrame):
    def __init__(self, master, width, height, fg_color, audioEngine:MAGE.AudioEngine):
        super().__init__(master, width, height, fg_color=fg_color)
        self.grid_rowconfigure(0, weight=1)
        self.grid_propagate(False) # Keep size fixed

        self.audioEngine = audioEngine

        self.sliders = []
        self.GEQ_properties = self.audioEngine.effects_chain["GEQ"]["properties"]

        self.frame_height = height

        for col_index, channel in enumerate(self.GEQ_properties):
            self.grid_columnconfigure(col_index, weight=0)
            slider = EQSlider(
                self,
                channel=channel,
                audioEngine=audioEngine,
                index=col_index,
                height=self.frame_height
            )
            slider.grid(row=0, column=col_index, padx=0, pady=0, sticky="ns")
            self.sliders.append(slider)

# * Input Device Select Class
class InputDeviceSelect(ctk.CTkFrame):
    def __init__(self, master, width, height, fg_color, audioEngine:MAGE.AudioEngine):
        super().__init__(master, width, height, fg_color=fg_color)

        self.label = ctk.CTkLabel(
            self,
            text_color="#FFFFFF", 
            width=40, 
            text="Input",
            font=("JetBrains Mono", 20) # (font, font size)
        )
        self.label.place(relx=0.5, rely=0.05, anchor="n")

        self.options = ctk.CTkSegmentedButton(
            self,
            values=["File", "Mic Input"],
            command=self._on_option_change
        )
        self.options.place(relx=0.5, rely=0.2, anchor="n")

        # File path input (shown when "File" is selected)
        self.file_entry = ctk.CTkEntry(
            self,
            placeholder_text="Enter file path...",
            width=width-20,
            font=("JetBrains Mono", 12),
        )

        inputDevices = audioEngine.list_input_devices()

        # Mic dropdown (shown when "Mic Input" is selected)
        self.mic_dropdown = ctk.CTkOptionMenu(
            self,
            values=inputDevices,
            width=width-20,
            dynamic_resizing=False,
            font=("JetBrains Mono", 12),
        )

        # Set default value and sync visibility on startup
        self.options.set("File")
        self._on_option_change("File")

    def _on_option_change(self, selected_value: str):
        if selected_value == "File":
            self.mic_dropdown.place_forget()
            self.file_entry.place(relx=0.5, rely=0.35, anchor="n")
        elif selected_value == "Mic Input":
            self.file_entry.place_forget()
            self.mic_dropdown.place(relx=0.5, rely=0.35, anchor="n")

# * Output Device Select Class
class OutputDeviceSelect(ctk.CTkFrame):
    def __init__(self, master, width, height, fg_color):
        super().__init__(master, width, height, fg_color=fg_color)

        self.effect_control = FloatSpinbox(self)

# * Effects Controls Class
class EffectsControls(ctk.CTkFrame):
    def __init__(self, master, width, height, fg_color, audioEngine:MAGE.AudioEngine, effect:str):
        super().__init__(master, width, height, fg_color=fg_color)
        self.audioEngine = audioEngine
        self.effect = effect

        self.effect_label = ctk.CTkLabel(
            self,
            text_color="#FFFFFF", 
            width=100, 
            height=100, 
            text=self.effect,
            font=("JetBrains Mono", 28) # (font, font size)
        )
        self.effect_label.place(relx=0.23, rely=0.5, anchor="e")

        # * TOGGLE ENABLE BUTTON
        self.toggle_enable_btn = ctk.CTkButton(self, text="Enable", command=self.toggle_enable)
        self.toggle_enable_btn.place(relx=0.55, rely=0.5, anchor="e")

        # * Spinbox to adjust effects
        initial_value = self.audioEngine.effects_chain[self.effect]["properties"][0]
        step_size = 0.1
        if self.effect != "GAIN":
            step_size = 100

        self.effect_control = FloatSpinbox(self, width=150, step_size=step_size)
        self.effect_control.set(initial_value)
        self.effect_control.place(relx=0.6, rely=0.5, anchor="w")
        
        self._update_property()

    def _update_property(self):
        entry = self.audioEngine.effects_chain[self.effect]

        effect_property_val = self.effect_control.get()
        entry["properties"][0] = effect_property_val

        self.after(50, self._update_property)

    def toggle_enable(self):
        """
            Toggle the effect and change the text of the button
        """
        self.audioEngine.toggle_enable_effect

        is_enabled = self.audioEngine.effects_chain[self.effect]["enabled"]

        if is_enabled:
            self.toggle_enable_btn.configure(text="Enable")

        else:
            self.toggle_enable_btn.configure(text="Disable")

        self.audioEngine.effects_chain[self.effect]["enabled"] = not is_enabled


