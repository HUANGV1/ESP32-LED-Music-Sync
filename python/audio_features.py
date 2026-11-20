"""Band-energy, loudness, and onset extraction for the lighting pipeline.

The extractor runs once per audio chunk. Filter and envelope state are kept
between calls, which avoids discontinuities at chunk boundaries and makes
beat/onset detection depend on recent context rather than absolute volume.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.signal as signal


@dataclass(frozen=True)
class AudioFeatures:
    """Per-frame features consumed by the lighting engine.

    Band values are normalized to byte-sized intensities. `beat` is a transient
    event flag, not a continuous brightness value.
    """

    bass: int
    mid: int
    treble: int
    loudness: int
    beat: bool


class _BandAnalyzer:
    """IIR bandpass + RMS envelope for one frequency range."""

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
        # EMA weights on previous value: lower rises faster, higher falls slower.
        self.attack = attack
        self.release = release
        self.smoothed_rms = 0.0

        # Keep cutoff below Nyquist so high treble settings remain valid.
        nyquist = sample_rate / 2.0
        high_hz = min(high_hz, nyquist * 0.99)

        # SOS form is numerically stable for real-time IIR filtering.
        self.sos = signal.butter(
            4,
            [low_hz, high_hz],
            btype="bandpass",
            fs=sample_rate,
            output="sos",
        )
        self.filter_state = np.zeros((self.sos.shape[0], 2))

    def update(self, mono: np.ndarray) -> float:
        """Return smoothed RMS for this band and update filter memory."""
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


class _OnsetDetector:
    """Bass-onset detector for head-nod style pulses.

    A beat is emitted when bass intensity jumps well above its recent baseline.
    This avoids treating sustained loud bass as repeated beats.
    """

    def __init__(
        self,
        threshold_multiplier: float,
        min_delta: int,
        min_intensity: int,
        baseline_alpha: float,
        cooldown_frames: int,
    ) -> None:
        self.threshold_multiplier = threshold_multiplier
        self.min_delta = min_delta
        self.min_intensity = min_intensity
        self.baseline_alpha = baseline_alpha
        self.cooldown_frames = cooldown_frames

        self.baseline: float | None = None
        self.cooldown_remaining = 0

    def update(self, value: int) -> bool:
        if self.baseline is None:
            self.baseline = float(value)
            return False

        baseline = self.baseline
        threshold = max(
            self.min_delta,
            baseline * (self.threshold_multiplier - 1.0),
        )

        beat = (
            self.cooldown_remaining == 0
            and value >= self.min_intensity
            and (value - baseline) > threshold
        )

        if beat:
            self.cooldown_remaining = self.cooldown_frames
        elif self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1

        # Slow baseline tracks the song's local energy without chasing hits.
        self.baseline = (
            self.baseline_alpha * baseline
            + (1.0 - self.baseline_alpha) * value
        )

        return beat


class AudioFeatureExtractor:
    """Stateful analyzer shared by the lighting engine.

    Call `get_features` once per audio chunk. Recreating this per frame would
    reset filter state, smoothing envelopes, and onset history.
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
        beat_threshold_multiplier: float,
        beat_min_delta: int,
        beat_min_intensity: int,
        beat_baseline_alpha: float,
        beat_cooldown_frames: int,
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
        self.onset = _OnsetDetector(
            threshold_multiplier=beat_threshold_multiplier,
            min_delta=beat_min_delta,
            min_intensity=beat_min_intensity,
            baseline_alpha=beat_baseline_alpha,
            cooldown_frames=beat_cooldown_frames,
        )

    def get_features(self, audio_chunk: np.ndarray) -> AudioFeatures:
        mono = self._to_mono(audio_chunk)

        bass_rms = self.bass.update(mono)
        mid_rms = self.mid.update(mono)
        treble_rms = self.treble.update(mono)

        # Full-band RMS acts as a master brightness signal, not a color band.
        full_rms = float(np.sqrt(np.mean(np.square(mono))))
        alpha = self.attack if full_rms > self.smoothed_loudness else self.release
        self.smoothed_loudness = (
            alpha * self.smoothed_loudness + (1.0 - alpha) * full_rms
        )

        bass = self.bass.to_byte(bass_rms)
        mid = self.mid.to_byte(mid_rms)
        treble = self.treble.to_byte(treble_rms)
        loudness = max(
            0,
            min(255, int(round(self.smoothed_loudness * self.gain_loudness * 255))),
        )

        return AudioFeatures(
            bass=bass,
            mid=mid,
            treble=treble,
            loudness=loudness,
            beat=self.onset.update(bass),
        )

    @staticmethod
    def _to_mono(audio_chunk: np.ndarray) -> np.ndarray:
        if audio_chunk.ndim == 1:
            return audio_chunk
        return np.mean(audio_chunk, axis=1)
