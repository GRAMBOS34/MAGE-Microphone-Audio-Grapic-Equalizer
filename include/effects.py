import json
import librosa
import numpy as np
import soundfile as sf

DEFAULT_EFFECTS_FILEPATH = "effects.json"

# * --------------- EFFECTS IMPLEMENTATIONS ---------------------

# * Copied from gemini cuz i had no time icl
# ! This filter is basically a sharp drop at the cutoff
# TODO: figure out how to add that rolloff at the end
# ? might keep this for a low-shelf filter?
def high_pass_filter(data, samplerate, cutoff:int = 300) -> np.ndarray:
    gain = 0.1 # ! for no audio clipping, keep it between 0 and 1
    n_fft = 1024
    n_frames, n_channels = data.shape
    processed_channels = []

    # ! This only works in stereo
    for ch in range(n_channels):
        # Extract ALL frames for this specific channel (shape: (1024,))
        ch_data = data[:, ch]
        
        # Safety check
        if len(ch_data) < n_fft:
            processed_channels.append(ch_data)
            continue
            
        # STFT - Short-Time Fourier Transform & EQ
        D = librosa.stft(ch_data, n_fft=n_fft)
        frequencies = librosa.fft_frequencies(sr=samplerate, n_fft=n_fft)
        gain_curve = np.ones_like(frequencies) # Create the gain curve
        gain_curve[frequencies < cutoff] = gain # Adjust the gain curve
        D_eq = D * gain_curve[:, np.newaxis] # Apply the gain curve
        
        # ISTFT - Inverse Short-Time Fourier Transform
        # Basically reverses what we just did
        ch_eq = librosa.istft(D_eq, length=len(ch_data))
        processed_channels.append(ch_eq)
        
    # Reassemble back to (frames, channels) -> (1024, 2)
    y_eq = np.stack(processed_channels, axis=1)

    return y_eq

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

def process_effects(audio_chunk, samplerate:int, effects_chain:dict[str, float | list[list[float]]]) -> np.ndarray:
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
                current_audio_chunk = audio_gain(audio_chunk, gain)

        # * Apply High-Pass Filter
        if effect == "HPF":
            cutoff = effects_chain.get(effect)

            if isinstance(cutoff, int):
                current_audio_chunk = high_pass_filter(current_audio_chunk, samplerate, cutoff)

    return current_audio_chunk
