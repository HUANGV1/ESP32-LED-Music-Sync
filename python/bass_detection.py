"""
bass_detection.py
-----------------
Converts raw audio samples into a single brightness number (0-255).

Pipeline for each audio chunk:
  1. Convert stereo -> mono
  2. Bandpass-filter so only bass frequencies remain
  3. Measure energy of that bass signal (RMS)
  4. Smooth the energy so the LED does not flicker too harshly
  5. Scale + clamp into 0..255 for the ESP32 PWM LED
"""

# NumPy does fast math on whole arrays of samples at once.
import numpy as np

# SciPy's signal module designs and applies digital filters.
import scipy.signal as signal


class BassDetector:
    """
    Stateful bass detector.

    "Stateful" means it remembers filter history and smoothed RMS
    between chunks. That memory is required for clean continuous filtering.
    """

    def __init__(
        self,
        sample_rate: int,
        low_hz: int,
        high_hz: int,
        gain: float,
        smoothing: float,
    ) -> None:
        # Sensitivity multiplier used later when mapping RMS -> 0..255.
        self.gain = gain

        # How much of the previous RMS to keep when smoothing.
        # See the formula in get_intensity().
        self.smoothing = smoothing

        # Running/smoothed bass energy. Starts at silence.
        self.smoothed_rms = 0.0

        """
        Design a 4th-order Butterworth bandpass filter.

        butter(...) returns filter coefficients.
        We ask for "sos" format (second-order sections), which is
        numerically more stable than older b/a coefficient forms.

        Meaning of the arguments:
          4                 -> filter order (steeper = better separation)
          [low_hz, high_hz] -> keep frequencies between these two values
          btype="bandpass"  -> reject below low_hz AND above high_hz
          fs=sample_rate    -> tells SciPy what "Hz" means in sample units
          output="sos"      -> return second-order section coefficients

        After this, self.sos is a 2D array of filter coefficients.
        """
        self.sos = signal.butter(
            4,
            [low_hz, high_hz],
            btype="bandpass",
            fs=sample_rate,
            output="sos",
        )

        # Filter memory / initial conditions.
        # sosfilt needs previous internal state so filtering is continuous
        # across chunk boundaries (no clicks / reset artifacts).
        # Shape: (number_of_sections, 2)
        self.filter_state = np.zeros((self.sos.shape[0], 2))

    def get_intensity(self, audio_chunk: np.ndarray) -> int:
        """
        Take one audio chunk and return LED brightness 0..255.
        """

        # Step 1: collapse left/right into one mono waveform.
        mono = self._to_mono(audio_chunk)

        # Step 2: run the bandpass filter.
        # sosfilt returns:
        #   bass          -> filtered samples (mostly 40-150 Hz content)
        #   filter_state  -> updated memory for the next chunk
        bass, self.filter_state = signal.sosfilt(
            self.sos,
            mono,
            zi=self.filter_state,
        )

        # Step 3: measure signal energy with RMS.
        # RMS = Root Mean Square
        #   square each sample  -> np.square(bass)
        #   average those squares -> np.mean(...)
        #   take square root      -> np.sqrt(...)
        # Result is a single float representing "how strong is the bass".
        rms = float(np.sqrt(np.mean(np.square(bass))))

        # Step 4: exponential moving average (EMA) smoothing.
        # New smoothed value blends previous and current RMS:
        #   smoothed = a * old + (1 - a) * new
        # where a = self.smoothing
        self.smoothed_rms = (
            self.smoothing * self.smoothed_rms
            + (1.0 - self.smoothing) * rms
        )

        # Step 5: convert energy into an 8-bit brightness.
        # Multiply by gain (sensitivity) and by 255 (PWM max).
        intensity = self.smoothed_rms * self.gain * 255

        # Clamp into legal range and cast to int for UDP/ESP32.
        return max(0, min(255, int(intensity)))

    def _to_mono(self, audio_chunk: np.ndarray) -> np.ndarray:
        """
        Convert stereo audio to mono by averaging left and right channels.

        Possible input shapes:
          (N,)   -> already mono
          (N, 2) -> stereo: column 0 = left, column 1 = right
        """

        # ndim == 1 means a 1D array, so it is already mono.
        if audio_chunk.ndim == 1:
            return audio_chunk

        # axis=1 means "average across channels for each time sample".
        # Result shape becomes (N,), one mono sample per time step.
        return np.mean(audio_chunk, axis=1)
