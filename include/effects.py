import librosa
import numpy as np
import soundfile as sf

# * Copied from gemini cuz i had no time icl
def high_pass_filter(data, samplerate, cutoff=300, gain=0.1):
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
            
        # STFT & EQ
        D = librosa.stft(ch_data, n_fft=n_fft)
        frequencies = librosa.fft_frequencies(sr=samplerate, n_fft=n_fft)
        gain_curve = np.ones_like(frequencies)
        gain_curve[frequencies < cutoff] = gain
        D_eq = D * gain_curve[:, np.newaxis]
        
        # ISTFT
        ch_eq = librosa.istft(D_eq, length=len(ch_data))
        processed_channels.append(ch_eq)
        
    # Reassemble back to (frames, channels) -> (1024, 2)
    y_eq = np.stack(processed_channels, axis=1)

    return y_eq