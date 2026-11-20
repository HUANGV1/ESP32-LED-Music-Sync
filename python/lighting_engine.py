"""Map `AudioFeatures` to PWM-ready RGB for the ESP32.

Base color comes from band energy:
  bass -> R, mid -> G, treble -> B

Beat events add a short white flash overlay. Keeping this in the display layer
lets onset detection stay about "when did a hit happen" while lighting decides
how visible that hit should be.
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
    """Stateful RGB mapper with smooth color and sharp beat accents."""

    def __init__(
        self,
        color_attack: float,
        color_release: float,
        color_deadzone: int,
        loudness_floor: float,
        beat_flash_intensity: int,
        beat_flash_decay: float,
    ) -> None:
        self.color_attack = color_attack
        self.color_release = color_release
        self.color_deadzone = color_deadzone
        self.loudness_floor = loudness_floor
        self.beat_flash_intensity = beat_flash_intensity
        self.beat_flash_decay = beat_flash_decay

        self.last_rgb = RgbColor(0, 0, 0)
        self.smooth_red = 0.0
        self.smooth_green = 0.0
        self.smooth_blue = 0.0
        self.beat_flash = 0.0

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

        if features.beat:
            self.beat_flash = max(self.beat_flash, self.beat_flash_intensity)

        # Beat flash bypasses color smoothing so hits feel immediate.
        red = self._clamp_byte(self.smooth_red + self.beat_flash)
        green = self._clamp_byte(self.smooth_green + self.beat_flash)
        blue = self._clamp_byte(self.smooth_blue + self.beat_flash)

        self.beat_flash *= self.beat_flash_decay

        # Suppress sub-threshold channel jitter, but never suppress beat flashes.
        if (
            not features.beat
            and abs(red - self.last_rgb.red) < self.color_deadzone
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

    @staticmethod
    def _clamp_byte(value: float) -> int:
        return max(0, min(255, int(round(value))))
