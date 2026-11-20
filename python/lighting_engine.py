"""
Map `AudioFeatures` to PWM-ready RGB for the ESP32.

Color assignment is intentional and fixed for v1:
  bass -> R, mid -> G, treble -> B
Loudness scales all channels so quiet sections dim without zeroing hue.
"""

from __future__ import annotations

from dataclasses import dataclass

from audio_features import AudioFeatures


@dataclass(frozen=True)
class RgbColor:
    red: int
    green: int
    blue: int


class LightingEngine:
    """Stateful RGB mapper with a second-stage envelope and output deadzone.

    Band energies are already attack/release-smoothed upstream. This stage
    smooths the display channels so channel crossfade does not shimmer when
    band ratios jitter at low amplitude.
    """

    def __init__(
        self,
        color_attack: float,
        color_release: float,
        color_deadzone: int,
        loudness_floor: float,
    ) -> None:
        self.color_attack = color_attack
        self.color_release = color_release
        self.color_deadzone = color_deadzone
        # Keep some residual brightness when loudness ≈ 0; 0.0 allows full black.
        self.loudness_floor = loudness_floor

        self.last_rgb = RgbColor(0, 0, 0)
        self.smooth_red = 0.0
        self.smooth_green = 0.0
        self.smooth_blue = 0.0

    def get_rgb(self, features: AudioFeatures) -> RgbColor:
        loudness_scale = self.loudness_floor + (1.0 - self.loudness_floor) * (
            features.loudness / 255.0
        )

        target_red = features.bass * loudness_scale
        target_green = features.mid * loudness_scale
        target_blue = features.treble * loudness_scale

        self.smooth_red = self._smooth(self.smooth_red, target_red)
        self.smooth_green = self._smooth(self.smooth_green, target_green)
        self.smooth_blue = self._smooth(self.smooth_blue, target_blue)

        red = max(0, min(255, int(round(self.smooth_red))))
        green = max(0, min(255, int(round(self.smooth_green))))
        blue = max(0, min(255, int(round(self.smooth_blue))))

        # Suppress sub-threshold channel noise that would otherwise spam UDP.
        if (
            abs(red - self.last_rgb.red) < self.color_deadzone
            and abs(green - self.last_rgb.green) < self.color_deadzone
            and abs(blue - self.last_rgb.blue) < self.color_deadzone
        ):
            return self.last_rgb

        rgb = RgbColor(red=red, green=green, blue=blue)
        self.last_rgb = rgb
        return rgb

    def _smooth(self, current: float, target: float) -> float:
        alpha = self.color_attack if target > current else self.color_release
        return alpha * current + (1.0 - alpha) * target
