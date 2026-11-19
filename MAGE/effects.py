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
def high_pass_filter(data: np.ndarray, samplerate: int, cutoff: int = 300, zi_state=None) -> tuple[np.ndarray, np.ndarray]:
    gain = 0.7  # Keep between 0 and 1 to prevent clipping
    n_frames, n_channels = data.shape

    # Build a Butterworth filter, this basically builds the gain curve we want
    # sos = Sixth-Order Sections, two is too subtle 
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

def low_pass_filter(data: np.ndarray, samplerate: int, cutoff: int = 8000, zi_state=None) -> tuple[np.ndarray, np.ndarray]:
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

# * ---------------- EFFECTS FILE READ AND WRITE ---------------------

# TODO: Make function to modify the effects file

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

        effects_chain = data["effects_chain"]

    return effects_chain

def process_effects(
        audio_chunk, 
        samplerate:int,
        effects_chain:dict,
        previous_zi_state:np.ndarray | None = None
) -> tuple[np.ndarray, np.ndarray | None]:
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

            if isinstance(cutoff, int):
                filtered_audio = high_pass_filter(current_audio_chunk, samplerate, cutoff, previous_zi_state)
                current_audio_chunk = filtered_audio[0]
                previous_zi_state = filtered_audio[1]

         # * Apply Low-Pass Filter
        if effect == "LPF" and is_enabled:
            cutoff = entry["properties"][0]

            if isinstance(cutoff, int):
                filtered_audio = low_pass_filter(current_audio_chunk, samplerate, cutoff, previous_zi_state)
                current_audio_chunk = filtered_audio[0]
                previous_zi_state = filtered_audio[1]

    return current_audio_chunk, previous_zi_state