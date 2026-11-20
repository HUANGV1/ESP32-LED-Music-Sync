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
# Typical: 1024-65535. Keep matched with firmware (default 4210).
UDP_PORT = 4210

# --- Capture -----------------------------------------------------------------

# SAMPLE_RATE is how many audio samples are captured per second.
# Typical: 44100 or 48000.
SAMPLE_RATE = 44100

# CHUNK_SIZE is how many samples are analyzed at once. 2048 is ~46 ms at
# 44.1 kHz. Smaller = lower latency but noisier; larger = smoother but laggier.
# Typical: 1024, 2048, 4096.
CHUNK_SIZE = 2048

# --- Band edges (Hz) ---------------------------------------------------------

# Bass band. This mostly captures kick drums, sub bass, and low bass notes.
# Typical: low 20-60, high 100-200.
BASS_LOW_HZ = 40
BASS_HIGH_HZ = 150

# Mid band. This captures vocals, guitars, piano body, and most melodic content.
# Typical: low 100-200, high 1500-4000.
MID_LOW_HZ = 150
MID_HIGH_HZ = 2000

# Treble band. This captures hi-hats, cymbals, claps, synth sparkle, and air.
# Typical: low 1500-4000, high 8000-16000 (clamped under Nyquist).
TREBLE_LOW_HZ = 2000
TREBLE_HIGH_HZ = 10000

# --- Band gains --------------------------------------------------------------

# GAIN_BASS controls red-channel sensitivity because bass maps to red.
# Increase if kick/bass barely shows; decrease if red is always maxed.
# Range: ~2-30. Typical: 8-16.
GAIN_BASS = 12.0

# GAIN_MID controls green-channel sensitivity because mids map to green.
# Increase if vocals/guitars do not affect color enough.
# Range: ~2-30. Typical: 6-14.
GAIN_MID = 10.0

# GAIN_TREBLE controls blue-channel sensitivity because treble maps to blue.
# Increase if hi-hats/cymbals are too subtle; decrease if blue dominates.
# Range: ~2-30. Typical: 8-18.
GAIN_TREBLE = 14.0

# GAIN_LOUDNESS controls the overall brightness scaling from full-band volume.
# Increase for more volume-driven pulsing; decrease for steadier brightness.
# Range: ~2-20. Typical: 4-12.
GAIN_LOUDNESS = 8.0

# Shared envelope for band/loudness RMS.

# ATTACK is the smoothing amount used when audio energy rises.
# Lower = sharper, faster jumps. Higher = softer, slower increases.
# Range: 0.0-0.95. Typical: 0.05-0.40.
ATTACK = 0.15

# RELEASE is the smoothing amount used when audio energy falls.
# Higher = slower fade and less flicker. Lower = drops faster after hits.
# Range: 0.0-0.98. Typical: 0.70-0.95.
RELEASE = 0.85

# --- Beat / onset detection --------------------------------------------------

# Beat detection watches for bass intensity jumps above a slow local baseline.
# It is separate from bass brightness: it tries to answer "did a hit just occur?"

# BEAT_THRESHOLD_MULTIPLIER sets the relative jump needed over the baseline.
# Higher = fewer beat triggers. Lower = more sensitive, possibly false hits.
# Range: 1.05-2.0. Typical: 1.15-1.50.
BEAT_THRESHOLD_MULTIPLIER = 1.30

# BEAT_MIN_DELTA is the minimum absolute bass jump required, in 0-255 units.
# Raise if the terminal shows BEAT too often on small bass wiggles.
# Range: 4-60. Typical: 10-30.
BEAT_MIN_DELTA = 16

# BEAT_MIN_INTENSITY ignores beat detection until bass is at least this strong.
# Raise to avoid false beats in quiet sections; lower if real kicks are missed.
# Range: 0-120. Typical: 10-40.
BEAT_MIN_INTENSITY = 24

# BEAT_BASELINE_ALPHA controls how slowly the local bass baseline adapts.
# Higher = baseline changes slower, good for detecting sudden hits.
# Lower = baseline follows the song faster, which can reduce false positives.
# Range: 0.70-0.99. Typical: 0.85-0.96.
BEAT_BASELINE_ALPHA = 0.92

# BEAT_COOLDOWN_FRAMES blocks another beat trigger for this many audio chunks.
# At CHUNK_SIZE=2048, 4 frames is roughly 184 ms. Raise if double-triggering.
# Range: 1-12. Typical: 3-6.
BEAT_COOLDOWN_FRAMES = 4

# --- Lighting mode -----------------------------------------------------------

# LIGHTING_MODE chooses how base color is produced.
#   "bands" -> bass=red, mid=green, treble=blue (frequency-reactive color)
#   "flow"  -> hue slowly cycles through the rainbow; loudness + beat still apply
# Options: "bands" | "flow"
LIGHTING_MODE = "flow"

# COLOR_FLOW_SPEED is degrees of hue advanced per second in "flow" mode.
# Higher = faster rainbow cycle. Lower = slower color drift.
# Range: 5-180. Typical: 20-90.
# Ignored when LIGHTING_MODE = "bands".
COLOR_FLOW_SPEED = 60.0

# FLOW_BRIGHTNESS_CEILING caps baseline brightness in flow mode (0.0-1.0).
# Lower = dimmer resting color and more room for beat flashes to stay on-hue.
# Higher = brighter baseline, but beat boosts clip toward white sooner.
# Range: 0.20-1.0. Typical: 0.35-0.65.
# Ignored when LIGHTING_MODE = "bands".
FLOW_BRIGHTNESS_CEILING = 0.2

# --- Display-stage RGB -------------------------------------------------------

# These apply after audio analysis. They smooth final visible color without
# changing the underlying band/beat detection.

# COLOR_ATTACK is smoothing for final RGB rising toward brighter values.
# Lower = sharper visible color jumps. Higher = softer transitions.
# Range: 0.0-0.95. Typical: 0.10-0.40.
COLOR_ATTACK = 0.22

# COLOR_RELEASE is smoothing for final RGB falling toward darker values.
# Higher = longer glow/fade. Lower = quicker drop after peaks.
# Range: 0.0-0.98. Typical: 0.70-0.95.
COLOR_RELEASE = 0.86

# COLOR_DEADZONE ignores tiny final RGB changes in 0-255 channel units.
# Higher = less shimmer but less tiny detail. Lower = more responsive.
# Range: 0-15. Typical: 1-6.
COLOR_DEADZONE = 3

# LOUDNESS_FLOOR is the minimum brightness multiplier when loudness is low.
# 0.0 allows black between quiet parts; higher keeps a constant faint glow.
# Range: 0.0-0.50. Typical: 0.05-0.20.
LOUDNESS_FLOOR = 0.12

# BEAT_FLASH_INTENSITY boosts the *current* color on a beat (not white).
# Gain formula: multiply RGB by (1 + intensity/100).
#   50  ≈ 1.5x brighter same color
#   100 ≈ 2.0x brighter same color
# Range: 0-200. Typical: 50-140. Above ~200 usually just clips.
BEAT_FLASH_INTENSITY = 100

# BEAT_FLASH_DECAY controls how quickly the beat flash fades each frame.
# Lower = shorter/snappier flash. Higher = longer flash trail.
# Range: 0.20-0.90. Typical: 0.40-0.70.
BEAT_FLASH_DECAY = 0.55
