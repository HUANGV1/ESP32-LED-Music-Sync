"""
Runtime tunables for capture, DSP, and lighting.

Keep secrets (Wi-Fi) out of this file; only put values that are safe to commit
and frequently retuned while iterating on visual response.
"""

# --- Network -----------------------------------------------------------------
ESP32_IP = "192.168.2.181"
UDP_PORT = 4210  # must match firmware

# --- Capture -----------------------------------------------------------------
SAMPLE_RATE = 44100
CHUNK_SIZE = 2048  # ~46 ms @ 44.1 kHz; lower latency vs noisier RMS tradeoff

# --- Band edges (Hz) ---------------------------------------------------------
BASS_LOW_HZ = 40
BASS_HIGH_HZ = 150

MID_LOW_HZ = 150
MID_HIGH_HZ = 2000

TREBLE_LOW_HZ = 2000
TREBLE_HIGH_HZ = 10000  # clamped under Nyquist in the analyzer

# --- Band gains --------------------------------------------------------------
# Applied after RMS; raise a band if that channel looks chronically dim.
GAIN_BASS = 12.0
GAIN_MID = 10.0
GAIN_TREBLE = 14.0
GAIN_LOUDNESS = 8.0

# Shared envelope for band/loudness RMS (weight retained from previous sample).
ATTACK = 0.45
RELEASE = 0.80

# --- Display-stage RGB -------------------------------------------------------
# Separate from band envelopes so hue can settle without retuning kick response.
COLOR_ATTACK = 0.55
COLOR_RELEASE = 0.88
COLOR_DEADZONE = 3

# Maps loudness∈[0,1] into [LOUDNESS_FLOOR, 1] before scaling RGB.
LOUDNESS_FLOOR = 0.12
