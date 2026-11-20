"""
audio_capture.py
----------------
Captures whatever Windows is currently playing (Spotify, YouTube, games...)

Key idea: WASAPI loopback
  - Windows can expose your speaker output as if it were a microphone.
  - "record" the speaker stream without needing a physical mic.
  - That captured audio becomes the input to bass detection.
"""

# Iterator is only used for type hints: "this function yields values forever".
from collections.abc import Iterator

# NumPy arrays are what SoundCard returns for audio samples.
import numpy as np

# SoundCard wraps Windows audio APIs (WASAPI) in a simple Python interface.
import soundcard as sc


class AudioCapture:
    """
    Finds your default speaker and opens a loopback recorder on it.
    """

    def __init__(self, sample_rate: int, chunk_size: int) -> None:
        # Store how fast and how large each audio grab should be.
        # sample_rate: samples per second (e.g. 44100)
        # chunk_size:  samples per batch (e.g. 2048)
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size

        # Ask SoundCard for the current default playback device.
        # Example name: "Speakers (Realtek Audio)"
        self.speaker = sc.default_speaker()

        # Create a "microphone" object that is actually the speaker loopback.
        # include_loopback=True is the important part:
        # it means "capture what this speaker is outputting".
        self.loopback_microphone = sc.get_microphone(
            id=str(self.speaker.name),
            include_loopback=True,
        )

    def chunks(self) -> Iterator[np.ndarray]:
        """
        Infinite generator that yields one stereo audio chunk at a time.

        Each yielded value is a NumPy array with shape:
          (chunk_size, 2)
        meaning:
          - chunk_size rows (time samples)
          - 2 columns (left channel, right channel)

        Sample values are floating-point amplitudes, typically around -1.0..1.0.
        """

        print(f"Capturing system audio from: {self.speaker.name}")

        # Open a recorder context.
        # samplerate=self.sample_rate tells Windows how fast to sample.
        # channels=2 means stereo capture (left + right).
        # The "with" block automatically starts and later cleans up the stream.
        with self.loopback_microphone.recorder(
            samplerate=self.sample_rate,
            channels=2,
        ) as recorder:
            # Forever loop: keep grabbing the next chunk of live audio.
            while True:
                # record(numframes=N) blocks until N samples are available,
                # then returns those samples as a NumPy array.
                # yield pauses this function and hands the array to the caller
                # (main.py). When the caller asks for the next chunk, we resume.
                yield recorder.record(numframes=self.chunk_size)
