import json
import numpy as np
from scipy import signal
import soundfile as sf

DEFAULT_EFFECTS_FILEPATH = "effects.json"

# * --------------- EFFECTS IMPLEMENTATIONS ---------------------

# * Copied from gemini cuz i had no time icl
# ! This filter is basically a sharp drop at the cutoff
# TODO: figure out how to add that rolloff at the end
def high_pass_filter(data: np.ndarray, samplerate: int, cutoff: int = 300, zi_state=None) -> tuple[np.ndarray, np.ndarray]:
    """
    Click-free high-pass filter for live streaming using Second-Order Sections (SOS).
    """
    gain = 0.1  # Keep between 0 and 1 to prevent clipping
    n_frames, n_channels = data.shape

    # 1. Design a Butterworth high-pass filter (2nd order is usually plenty for basic HPF)
    # sos shape: (n_sections, 6)
    sos = signal.butter(N=2, Wn=cutoff, btype='high', fs=samplerate, output='sos')

    # 2. Initialize or retrieve filter states (zi) for continuity across chunks
    # sosfilt_zi maintains the filter's internal delay memory per section and channel
    if zi_state is None:
        # shape for sosfilt_zi: (n_sections, 2, n_channels)
        zi_state = signal.sosfilt_zi(sos)
        # Expand zi to match channels if necessary, or let sosfilt handle it
        zi_state = np.repeat(zi_state[:, :, np.newaxis], n_channels, axis=2)

    processed_channels = []
    new_zi_states = []

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

def audio_gain(data:np.ndarray, gain:float = 0.1) -> np.ndarray:
    audio_chunk = data * gain

    return audio_chunk

# * ---------------- EFFECTS FILE READ AND WRITE ---------------------

# TODO: Make function to modify the effects file

def load_effects(filepath:str = DEFAULT_EFFECTS_FILEPATH) -> dict[str, float | list[list[float]]]:
    effects_chain = {}

    # Read data (read-only privileges)
    with open(filepath, "r") as file:
        data = json.load(file)

        effects_chain = data["effects_chain"]

    return effects_chain

"""
    Format

    Gain
    "GAIN" : [gain]

    HPF/LPF:
    "HPF" : [cutoff]

    Graphic Equalizer (not exactly sure of the spacing yet):
    [freq, gain, Q]
    "GEQ" : [[20, 0, 1], [50, 0, 1], [130, 0, 1], ..., [12000, 0, 1], [14000, 0, 1], [16600, 0, 1]]

    ? consider having id's instead so that we can chain duplicates? idk though
    ? like having PAG -> GEQ -> HPF -> PAG

    The output fader is controlled in MAGE.audio_playback though
"""
def process_effects(
        audio_chunk, 
        samplerate:int,
        effects_chain:dict[str, float | list[list[float]]], 
        previous_zi_state:np.ndarray | None
) -> tuple[np.ndarray, np.ndarray | None]:
    
    # So we don't waste time on an empty array
    if len(effects_chain) == 0:
        return audio_chunk

    current_audio_chunk = audio_chunk

    for effect in effects_chain:
        # * Apply gain
        # * This is the first check so that it doesn't accidentally add gain on gain
        if effect == "GAIN":
            gain = effects_chain.get(effect)

            if isinstance(gain, float):
                current_audio_chunk = audio_gain(current_audio_chunk, gain)

        # * Apply High-Pass Filter
        if effect == "HPF":
            cutoff = effects_chain.get(effect)

            if isinstance(cutoff, int):
                filtered_audio = high_pass_filter(current_audio_chunk, samplerate, cutoff, previous_zi_state)
                current_audio_chunk = filtered_audio[0]
                previous_zi_state = filtered_audio[1]

    return current_audio_chunk, previous_zi_state