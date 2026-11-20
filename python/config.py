"""Runtime tunables for capture, DSP, beat detection, and lighting.

Only values that are safe to commit and useful during visual tuning belong
here. Wi-Fi credentials stay in the firmware's gitignored `secrets.h`.
"""

# --- Network -----------------------------------------------------------------

# ESP32_IP is the address printed by the ESP32 Serial Monitor after Wi-Fi
# connects. Python sends UDP packets here, so the LED will not respond if this
# points at the wrong device.
ESP32_IP = "192.168.2.181"

# UDP_PORT must match UDP_PORT in the ESP32 firmware. It is the "mailbox" the
# ESP32 listens on for RGB frames.
UDP_PORT = 4210

# --- Capture -----------------------------------------------------------------

# SAMPLE_RATE is how many audio samples are captured per second. 44100 is a
# good default because most music is already 44.1 kHz.
SAMPLE_RATE = 44100

# CHUNK_SIZE is how many samples are analyzed at once. 2048 is ~46 ms at
# 44.1 kHz. Smaller = lower latency but noisier; larger = smoother but laggier.
CHUNK_SIZE = 2048

# --- Band edges (Hz) ---------------------------------------------------------

# Bass band. This mostly captures kick drums, sub bass, and low bass notes.
BASS_LOW_HZ = 40
BASS_HIGH_HZ = 150

# Mid band. This captures vocals, guitars, piano body, and most melodic content.
MID_LOW_HZ = 150
MID_HIGH_HZ = 2000

# Treble band. This captures hi-hats, cymbals, claps, synth sparkle, and air.
TREBLE_LOW_HZ = 2000
TREBLE_HIGH_HZ = 10000

# --- Band gains --------------------------------------------------------------

# GAIN_BASS controls red-channel sensitivity because bass maps to red.
# Increase if kick/bass barely shows; decrease if red is always maxed.
GAIN_BASS = 12.0

# GAIN_MID controls green-channel sensitivity because mids map to green.
# Increase if vocals/guitars do not affect color enough.
GAIN_MID = 10.0

# GAIN_TREBLE controls blue-channel sensitivity because treble maps to blue.
# Increase if hi-hats/cymbals are too subtle; decrease if blue dominates.
GAIN_TREBLE = 14.0

# GAIN_LOUDNESS controls the overall brightness scaling from full-band volume.
# Increase for more volume-driven pulsing; decrease for steadier brightness.
GAIN_LOUDNESS = 8.0

# Shared envelope for band/loudness RMS.

# ATTACK is the smoothing amount used when audio energy rises.
# Lower = sharper, faster jumps. Higher = softer, slower increases.
ATTACK = 0.15

# RELEASE is the smoothing amount used when audio energy falls.
# Higher = slower fade and less flicker. Lower = drops faster after hits.
RELEASE = 0.85

# --- Beat / onset detection --------------------------------------------------

# Beat detection watches for bass intensity jumps above a slow local baseline.
# It is separate from bass brightness: it tries to answer "did a hit just occur?"

# BEAT_THRESHOLD_MULTIPLIER sets the relative jump needed over the baseline.
# Higher = fewer beat triggers. Lower = more sensitive, possibly false hits.
BEAT_THRESHOLD_MULTIPLIER = 1.30

# BEAT_MIN_DELTA is the minimum absolute bass jump required, in 0-255 units.
# Raise if the terminal shows BEAT too often on small bass wiggles.
BEAT_MIN_DELTA = 16

# BEAT_MIN_INTENSITY ignores beat detection until bass is at least this strong.
# Raise to avoid false beats in quiet sections; lower if real kicks are missed.
BEAT_MIN_INTENSITY = 24

# BEAT_BASELINE_ALPHA controls how slowly the local bass baseline adapts.
# Higher = baseline changes slower, good for detecting sudden hits.
# Lower = baseline follows the song faster, which can reduce false positives.
BEAT_BASELINE_ALPHA = 0.92

# BEAT_COOLDOWN_FRAMES blocks another beat trigger for this many audio chunks.
# At CHUNK_SIZE=2048, 4 frames is roughly 184 ms. Raise if double-triggering.
BEAT_COOLDOWN_FRAMES = 4

# --- Display-stage RGB -------------------------------------------------------

# These apply after audio analysis. They smooth final visible color without
# changing the underlying band/beat detection.

# COLOR_ATTACK is smoothing for final RGB rising toward brighter values.
# Lower = sharper visible color jumps. Higher = softer transitions.
COLOR_ATTACK = 0.22

# COLOR_RELEASE is smoothing for final RGB falling toward darker values.
# Higher = longer glow/fade. Lower = quicker drop after peaks.
COLOR_RELEASE = 0.86

# COLOR_DEADZONE ignores tiny final RGB changes in 0-255 channel units.
# Higher = less shimmer but less tiny detail. Lower = more responsive.
COLOR_DEADZONE = 3

# LOUDNESS_FLOOR is the minimum brightness multiplier when loudness is low.
# 0.0 allows black between quiet parts; higher keeps a constant faint glow.
LOUDNESS_FLOOR = 0.12

# BEAT_FLASH_INTENSITY is added to all RGB channels when a beat is detected.
# Higher = brighter white flash on hits. Lower = subtler pulse.
BEAT_FLASH_INTENSITY = 90

# BEAT_FLASH_DECAY controls how quickly the beat flash fades each frame.
# Lower = shorter/snappier flash. Higher = longer flash trail.
BEAT_FLASH_DECAY = 0.55
