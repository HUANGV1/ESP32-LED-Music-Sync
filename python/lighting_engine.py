"""Map `AudioFeatures` to PWM-ready RGB for the ESP32.

Two base-color modes:
  bands -> bass=R, mid=G, treble=B
  flow  -> continuous hue cycle; loudness drives brightness of that hue

Beat events boost the *current* color intensity (not a white overlay), so
flow-mode flashes stay on-hue instead of washing out to white.
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass

from audio_features import AudioFeatures


@dataclass(frozen=True)
class RgbColor:
    red: int
    green: int
    blue: int


class LightingEngine:
    """Stateful RGB mapper with mode selection, smooth color, and beat accents."""

    def __init__(
        self,
        mode: str,
        color_flow_speed: float,
        frame_seconds: float,
        color_attack: float,
        color_release: float,
        color_deadzone: int,
        loudness_floor: float,
        flow_brightness_ceiling: float,
        beat_flash_intensity: int,
        beat_flash_decay: float,
    ) -> None:
        mode = mode.lower().strip()
        if mode not in {"bands", "flow"}:
            raise ValueError('LIGHTING_MODE must be "bands" or "flow"')

        self.mode = mode
        # Degrees of hue advanced each frame in flow mode.
        self.hue_step = color_flow_speed * frame_seconds
        self.color_attack = color_attack
        self.color_release = color_release
        self.color_deadzone = color_deadzone
        self.loudness_floor = loudness_floor
        self.flow_brightness_ceiling = max(0.05, min(1.0, flow_brightness_ceiling))
        self.beat_flash_intensity = beat_flash_intensity
        self.beat_flash_decay = beat_flash_decay

        self.hue_degrees = 0.0
        self.last_rgb = RgbColor(0, 0, 0)
        self.smooth_red = 0.0
        self.smooth_green = 0.0
        self.smooth_blue = 0.0
        self.beat_flash = 0.0

    def get_rgb(self, features: AudioFeatures) -> RgbColor:
        loudness_scale = self.loudness_floor + (1.0 - self.loudness_floor) * (
            features.loudness / 255.0
        )

        if self.mode == "flow":
            target_red, target_green, target_blue = self._flow_targets(
                features, loudness_scale
            )
        else:
            target_red = features.bass * loudness_scale
            target_green = features.mid * loudness_scale
            target_blue = features.treble * loudness_scale

        self.smooth_red = self._smooth(self.smooth_red, target_red)
        self.smooth_green = self._smooth(self.smooth_green, target_green)
        self.smooth_blue = self._smooth(self.smooth_blue, target_blue)

        if features.beat:
            self.beat_flash = max(self.beat_flash, float(self.beat_flash_intensity))

        # Multiply current color instead of adding equal R/G/B (which -> white).
        # Intensity 100 ≈ 2x brightness of the current hue/mix.
        flash_gain = 1.0 + (self.beat_flash / 100.0)
        red = self._clamp_byte(self.smooth_red * flash_gain)
        green = self._clamp_byte(self.smooth_green * flash_gain)
        blue = self._clamp_byte(self.smooth_blue * flash_gain)

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

    def _flow_targets(
        self, features: AudioFeatures, loudness_scale: float
    ) -> tuple[float, float, float]:
        """Advance hue and return RGB targets for the current flow color."""
        self.hue_degrees = (self.hue_degrees + self.hue_step) % 360.0

        # Brightness follows music; hue drifts independently.
        band_peak = max(features.bass, features.mid, features.treble) / 255.0
        intensity = 0.65 * (features.loudness / 255.0) + 0.35 * band_peak

        # Cap baseline so beat boosts have headroom without clipping to white.
        value = max(0.0, min(self.flow_brightness_ceiling, intensity * loudness_scale))

        red_f, green_f, blue_f = colorsys.hsv_to_rgb(
            self.hue_degrees / 360.0,
            1.0,
            value,
        )
        return red_f * 255.0, green_f * 255.0, blue_f * 255.0

    def _smooth(self, current: float, target: float) -> float:
        alpha = self.color_attack if target > current else self.color_release
        return alpha * current + (1.0 - alpha) * target

    @staticmethod
    def _clamp_byte(value: float) -> int:
        return max(0, min(255, int(round(value))))
