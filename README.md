# M.A.G.E - Microphone and Audio Graphic Equalizer

By: Vladimir Jumawan

## Problem Statement

Traditional audio processing tools often rely on crowded GUIs that are hard to read, especially at a glance. While this does pack more settings into a tight space, it makes it way harder to track what you’re focusing on without hovering your mouse over the knob. Not to mention that this number of features usually results in the tool running slowly during use. In addition to this, these tools are normally platform-dependent. Meaning a tool that may work in Linux may not work in Windows. Consequently, there is a need for a low-complexity, platform-agnostic audio processing tool that remains powerful enough to execute real-time audio equalization while being performant enough to run in reproducible cloud environments.

## Installation

1. Clone this repo with:

```
git clone https://github.com/GRAMBOS34/MAGE-Microphone-Audio-Grapic-Equalizer.git
```

2. Go into the directory and install the prerequisites using

```
pip install -r requirements.txt
```

3. Run the program using either

```
python main.py
```

or

```
python3 main.py
```

## Libraries Used

(properly cite them)
soundfile
sounddevice
numpy
librosa

## AI-Use Disclaimer

(draft)
I decided on these libraries mainly through the use of AI, but I am the one who wrote the logic using them
