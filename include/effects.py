import json
import librosa
import numpy as np
import soundfile as sf

DEFAULT_EFFECTS_FILEPATH = "effects.json"

def load_effects(audio_chunk, samplerate:int, filepath:str = DEFAULT_EFFECTS_FILEPATH):
    effects_chain = {}

    # Read data (read-only privileges)
    with open(DEFAULT_EFFECTS_FILEPATH, "r") as file:
        data = json.load(file)

        effects_chain = data["effects_chain"]

    # I somehow need to run every single effect here and return the final ndarray
    """
        Format

        HPF/LPF:
        "HPF" : [cutoff]

        Graphic Equalizer (not exactly sure of the spacing yet):
        [freq, gain, Q]
        "GEQ" : [[20, 0, 1], [50, 0, 1], [130, 0, 1], ..., [12000, 0, 1], [14000, 0, 1], [16600, 0, 1]]
    """

    return effects_chain

# * Copied from gemini cuz i had no time icl
# ! This filter is basically a sharp drop at the cutoff
# TODO: figure out how to add that rolloff at the end
def high_pass_filter(data, samplerate, cutoff=300):
    gain = 0.1
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