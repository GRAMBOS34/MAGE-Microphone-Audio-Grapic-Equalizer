import json
import numpy as np
from scipy import signal
import soundfile as sf

DEFAULT_EFFECTS_FILEPATH = "effects.json"

# * --------------- EFFECTS IMPLEMENTATIONS ---------------------

"""
    Copied from gemini because I couldn't think of an alternative to the FFT I previously used
    However, the comments below are explanations written in my own words

    This implementation actually avoids the crackling noise caused by the STFT (Short-Time Fourier Transform) 
    needs an overlap both forwards and backwards. This willnot be possible when a mic is used.

    This solution actually modifies the signal in the time domain rather than the frequency domain
"""
def high_pass_filter(
        data: np.ndarray, 
        samplerate: int, 
        cutoff: float = 300.0, 
        zi_state=None
    ) -> tuple[np.ndarray, np.ndarray]:
    gain = 0.7  # Keep between 0 and 1 to prevent clipping
    n_frames, n_channels = data.shape

    # Build a Butterworth filter, this basically builds the gain curve we want
    # sos = Second-Order Sections; N=2 is too subtle 
    sos = signal.butter(N=6, Wn=cutoff, btype='high', fs=samplerate, output='sos')

    # Retrieve or initialize zi_state
    # The zi state is used in the calculations of the biquad filter
    # This allows us to keep the "momentum" of changes even on the next chunk
    if zi_state is None:
        # shape for sosfilt_zi: (n_sections, 2, n_channels)
        zi_state = signal.sosfilt_zi(sos)
        # Expand zi to match channels if necessary, or let sosfilt handle it
        zi_state = np.repeat(zi_state[:, :, np.newaxis], n_channels, axis=2)

    processed_channels = []
    new_zi_states = []

    # We now use the zi_state to filter the sos so we can get the signal we want
    for ch in range(n_channels):
        ch_data = data[:, ch]
        
        # Extract the state for this specific channel: shape (n_sections, 2)
        ch_zi = zi_state[:, :, ch]
        
        # Apply filter statefully
        filtered_ch, ch_zi_new = signal.sosfilt(sos, ch_data, zi=ch_zi)
        
        # Apply gain
        filtered_ch = filtered_ch * gain
        
        processed_channels.append(filtered_ch)
        new_zi_states.append(ch_zi_new)

    # Reassemble channels: (frames, channels)
    y_eq = np.stack(processed_channels, axis=1)
    
    # Pack new states back into shape (n_sections, 2, n_channels)
    new_zi_states = np.stack(new_zi_states, axis=2)

    return y_eq, new_zi_states

def low_pass_filter(
        data: np.ndarray, 
        samplerate: int, 
        cutoff: float = 8000.0, 
        zi_state=None
    ) -> tuple[np.ndarray, np.ndarray]:
    gain = 0.7  # Keep between 0 and 1 to prevent clipping
    n_frames, n_channels = data.shape

    # Build a Butterworth filter, this basically builds the gain curve we want
    sos = signal.butter(N=6, Wn=cutoff, btype='low', fs=samplerate, output='sos')

    # Retrieve or initialize zi_state
    if zi_state is None:
        # shape for sosfilt_zi: (n_sections, 2, n_channels)
        zi_state = signal.sosfilt_zi(sos)
        # Expand zi to match channels if necessary, or let sosfilt handle it
        zi_state = np.repeat(zi_state[:, :, np.newaxis], n_channels, axis=2)

    processed_channels = []
    new_zi_states = []

    # We now use the zi_state to filter the sos so we can get the signal we want
    for ch in range(n_channels):
        ch_data = data[:, ch]
        
        # Extract the state for this specific channel: shape (n_sections, 2)
        ch_zi = zi_state[:, :, ch]
        
        # Apply filter statefully
        filtered_ch, ch_zi_new = signal.sosfilt(sos, ch_data, zi=ch_zi)
        
        # Apply gain
        filtered_ch = filtered_ch * gain
        
        processed_channels.append(filtered_ch)
        new_zi_states.append(ch_zi_new)

    # Reassemble channels: (frames, channels)
    y_eq = np.stack(processed_channels, axis=1)
    
    # Pack new states back into shape (n_sections, 2, n_channels)
    new_zi_states = np.stack(new_zi_states, axis=2)

    return y_eq, new_zi_states

def audio_gain(data:np.ndarray, gain:float) -> np.ndarray:
    """
        Adjusts signal gain

        Args:
        data : np.ndarray - Audio data
        gain : float = 0.1 - New audio gain
    """
    audio_chunk = data * gain

    return audio_chunk

# * --------------- GRAPHICAL EQ ---------------------
# ! AI was used to write these two functions, however, all the comments are all mine
# ! I only really did this due to the time crunch
def peaking_eq_sos_row(
        freq: float,
        gain_db: float,
        q: float,
        samplerate: int
    ) -> np.ndarray:
    """
        Build a single biquad peaking EQ section [b0, b1, b2, a0, a1, a2] (normalized so a0=1).
    """

    # Defines the highest frequency we can deal with
    nyquist = 0.5 * samplerate
    q_safe = max(float(q), 1e-3)

    # Bypass invalid frequencies with unity pass-through
    if freq <= 0.0 or freq >= nyquist:
        return np.array([1.0, 0.0, 0.0, 1.0, 0.0, 0.0], dtype=np.float32)

    # Convert gain db to amplitude factor
    a = 10.0 ** (float(gain_db) / 40.0)
    w0 = 2.0 * np.pi * float(freq) / float(samplerate)
    alpha = np.sin(w0) / (2.0 * q_safe)

    cos_w0 = np.cos(w0)
    b0 = 1.0 + alpha * a
    b1 = -2.0 * cos_w0
    b2 = 1.0 - alpha * a
    a0 = 1.0 + alpha / a
    a1 = -2.0 * cos_w0
    a2 = 1.0 - alpha / a

    return np.array([b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0], dtype=np.float32)

def graphical_eq(
        data: np.ndarray,
        samplerate: int, 
        properties_list: list[list[float]],
        previous_zi_state: np.ndarray | None = None
    ) -> tuple[np.ndarray, np.ndarray]:
    """
        Properties List format:
        properties_list = [
            [freq, gain, Q],
            [freq, gain, Q],
            ... 
        ]
        for a total of 16 elements
    """
    # Check if mono audio
    if data.ndim == 1:
        data = data[:, np.newaxis]

    n_frames, n_channels = data.shape

    # Build (16, 6) SOS matrix from each entry
    # Basically put all the bands in series
    sos = np.vstack([
        peaking_eq_sos_row(freq, gain_db, q, samplerate)
        for freq, gain_db, q in properties_list
    ])

    # Guard against a None/null zi_state
    expected_shape = (sos.shape[0], 2, n_channels)
    if previous_zi_state is None or previous_zi_state.shape != expected_shape:
        previous_zi_state = np.zeros(expected_shape, dtype=np.float32)

    # Put them all together
    y_out = np.empty_like(data, dtype=np.float64)
    new_zi = np.empty_like(previous_zi_state, dtype=np.float64)

    for ch in range(n_channels):
        y_out[:, ch], new_zi[:, :, ch] = signal.sosfilt(
            sos, data[:, ch], zi=previous_zi_state[:, :, ch]
        )

    return y_out, new_zi

# * ---------------- EFFECTS FILE READ AND WRITE ---------------------

def load_effects(filepath:str = DEFAULT_EFFECTS_FILEPATH) -> dict:
    """
        Loads the effects file and saves the enabled effects

        Args:
            filepath: str - the effects.json filepath

        Returns:
            effects_chain:dict - the dictionary of enabled effects
    """
    effects_chain = {}

    # Read data (read-only privileges)
    with open(filepath, "r") as file:
        data = json.load(file)

        effects_chain = data

    return effects_chain

def save_effects(effects_chain:dict, filepath:str = DEFAULT_EFFECTS_FILEPATH):
    """
        Writes effects to the effects.json

        Args:
            effects_chain:dict - the current effects chain
            filepath:str - filepath of the effects.json
    """
    with open(filepath, "w+") as file:
        formatted_effects_chain = effects_chain

        for effect in effects_chain:
            if effect == "GAIN": continue

            # ! This is honestly a pretty lazy fix
            # ! Because in some its a list, others its an ndarray?
            try:
                formatted_effects_chain[effect]["previous_zi_state"] = effects_chain[effect]["previous_zi_state"].tolist()
            except:
                formatted_effects_chain[effect]["previous_zi_state"] = effects_chain[effect]["previous_zi_state"]
        
        new_effects = json.dumps(formatted_effects_chain, indent=4)

        file.write(new_effects)

def process_effects(
        audio_chunk, 
        samplerate:int,
        effects_chain:dict
) -> np.ndarray:
    current_audio_chunk = audio_chunk

    for effect in effects_chain:
        entry = effects_chain[effect]
        is_enabled = entry.get("enabled")

        # * Apply gain
        if effect == "GAIN" and is_enabled:
            gain = entry["properties"][0]

            if isinstance(gain, float):
                current_audio_chunk = audio_gain(current_audio_chunk, gain)

        # * Apply High-Pass Filter
        if effect == "HPF" and is_enabled:
            cutoff = entry["properties"][0]
            raw_zi = entry.get("previous_zi_state")
            previous_zi_state = None if raw_zi is None else np.asarray(raw_zi)

            if isinstance(cutoff, float):
                filtered_audio = high_pass_filter(current_audio_chunk, samplerate, cutoff, previous_zi_state)
                current_audio_chunk = filtered_audio[0]
                entry["previous_zi_state"] = filtered_audio[1]

        # * Apply Low-Pass Filter
        if effect == "LPF" and is_enabled:
            cutoff = entry["properties"][0]
            raw_zi = entry.get("previous_zi_state")
            previous_zi_state = None if raw_zi is None else np.asarray(raw_zi)

            if isinstance(cutoff, float):
                filtered_audio = low_pass_filter(current_audio_chunk, samplerate, cutoff, previous_zi_state)
                current_audio_chunk = filtered_audio[0]
                entry["previous_zi_state"] = filtered_audio[1]

        # * Apply Graphical EQ
        if effect == "GEQ" and is_enabled:
            properties_list = entry["properties"]
            raw_zi = entry.get("previous_zi_state")
            previous_zi_state = None if raw_zi is None else np.asarray(raw_zi)

            filtered_audio = graphical_eq(current_audio_chunk, samplerate, properties_list, previous_zi_state=previous_zi_state)
            current_audio_chunk = filtered_audio[0]
            entry["previous_zi_state"] = filtered_audio[1]

    return current_audio_chunk