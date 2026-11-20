"""
Band-energy and loudness extraction for the lighting pipeline.

Operates on short WASAPI loopback frames. Filter state is preserved across
calls so bandpass filtering stays continuous at chunk boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.signal as signal


@dataclass(frozen=True)
class AudioFeatures:
    """Per-frame feature vector; each field is an 8-bit intensity [0, 255]."""

    bass: int
    mid: int
    treble: int
    loudness: int


class _BandAnalyzer:
    """IIR bandpass + RMS with asymmetric attack/release envelope."""

    def __init__(
        self,
        sample_rate: int,
        low_hz: float,
        high_hz: float,
        gain: float,
        attack: float,
        release: float,
    ) -> None:
        self.gain = gain
        # EMA weights on previous value: higher => slower tracking.
        self.attack = attack
        self.release = release
        self.smoothed_rms = 0.0

        # Keep cutoff below Nyquist; treble tops out near fs/2 at 44.1 kHz.
        nyquist = sample_rate / 2.0
        high_hz = min(high_hz, nyquist * 0.99)

        # SOS form avoids coefficient instability vs classic b/a for order-4.
        self.sos = signal.butter(
            4,
            [low_hz, high_hz],
            btype="bandpass",
            fs=sample_rate,
            output="sos",
        )
        self.filter_state = np.zeros((self.sos.shape[0], 2))

    def update(self, mono: np.ndarray) -> float:
        """Return smoothed RMS for this band; updates internal filter memory."""
        filtered, self.filter_state = signal.sosfilt(
            self.sos,
            mono,
            zi=self.filter_state,
        )
        rms = float(np.sqrt(np.mean(np.square(filtered))))

        alpha = self.attack if rms > self.smoothed_rms else self.release
        self.smoothed_rms = alpha * self.smoothed_rms + (1.0 - alpha) * rms
        return self.smoothed_rms

    def to_byte(self, rms: float) -> int:
        return max(0, min(255, int(round(rms * self.gain * 255))))


class AudioFeatureExtractor:
    """Stateful multi-band analyzer shared by the lighting engine.

    Call `get_features` once per audio chunk. Do not recreate per frame —
    filter and envelope state must survive across chunks.
    """

    def __init__(
        self,
        sample_rate: int,
        bass_range: tuple[int, int],
        mid_range: tuple[int, int],
        treble_range: tuple[int, int],
        gain_bass: float,
        gain_mid: float,
        gain_treble: float,
        gain_loudness: float,
        attack: float,
        release: float,
    ) -> None:
        self.gain_loudness = gain_loudness
        self.attack = attack
        self.release = release
        self.smoothed_loudness = 0.0

        self.bass = _BandAnalyzer(
            sample_rate, bass_range[0], bass_range[1], gain_bass, attack, release
        )
        self.mid = _BandAnalyzer(
            sample_rate, mid_range[0], mid_range[1], gain_mid, attack, release
        )
        self.treble = _BandAnalyzer(
            sample_rate,
            treble_range[0],
            treble_range[1],
            gain_treble,
            attack,
            release,
        )

    def get_features(self, audio_chunk: np.ndarray) -> AudioFeatures:
        """
        Args:
            audio_chunk: float samples, shape (N,) mono or (N, C) interleaved.
        """
        mono = self._to_mono(audio_chunk)

        bass_rms = self.bass.update(mono)
        mid_rms = self.mid.update(mono)
        treble_rms = self.treble.update(mono)

        # Full-band RMS used as a master brightness driver (not a bandpass).
        full_rms = float(np.sqrt(np.mean(np.square(mono))))
        alpha = self.attack if full_rms > self.smoothed_loudness else self.release
        self.smoothed_loudness = (
            alpha * self.smoothed_loudness + (1.0 - alpha) * full_rms
        )

        loudness_byte = max(
            0,
            min(255, int(round(self.smoothed_loudness * self.gain_loudness * 255))),
        )

        return AudioFeatures(
            bass=self.bass.to_byte(bass_rms),
            mid=self.mid.to_byte(mid_rms),
            treble=self.treble.to_byte(treble_rms),
            loudness=loudness_byte,
        )

    @staticmethod
    def _to_mono(audio_chunk: np.ndarray) -> np.ndarray:
        if audio_chunk.ndim == 1:
            return audio_chunk
        return np.mean(audio_chunk, axis=1)
