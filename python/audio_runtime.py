"""Shared audio -> lighting -> UDP runtime.

Used by:
  - `main.py` (standalone CLI)
  - `dashboard_server.py` (background thread under the web UI)
"""

from __future__ import annotations

import threading
import time
from typing import Any

from audio_capture import AudioCapture
from audio_features import AudioFeatureExtractor
from config import (
    BASS_HIGH_HZ,
    BASS_LOW_HZ,
    CHUNK_SIZE,
    ESP32_IP,
    MID_HIGH_HZ,
    MID_LOW_HZ,
    SAMPLE_RATE,
    TREBLE_HIGH_HZ,
    TREBLE_LOW_HZ,
    UDP_PORT,
)
from lighting_engine import LightingEngine
from settings_store import merged_settings, settings_mtime_ns
from udp_sender import UdpSender


def apply_pipeline_settings(
    features: AudioFeatureExtractor,
    lighting: LightingEngine,
    sender: UdpSender,
    frame_seconds: float,
) -> dict[str, Any]:
    settings = merged_settings()
    features.apply_runtime_settings(settings)
    lighting.apply_runtime_settings(settings, frame_seconds)
    sender.address = (str(settings["ESP32_IP"]), int(settings["UDP_PORT"]))
    return settings


class AudioRuntime:
    """Stoppable realtime loop for capture / analysis / UDP send."""

    def __init__(self, *, verbose: bool = True) -> None:
        self.verbose = verbose
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._error: str | None = None
        self._lock = threading.Lock()
        self._last_rgb = (0, 0, 0)
        self._last_beat = False
        self._running = False

    @property
    def running(self) -> bool:
        return self._running and self._thread is not None and self._thread.is_alive()

    @property
    def last_error(self) -> str | None:
        return self._error

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "running": self.running,
                "error": self._error,
                "rgb": list(self._last_rgb),
                "beat": self._last_beat,
            }

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._error = None
        self._thread = threading.Thread(
            target=self._run,
            name="audio-runtime",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float = 3.0) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout)
        self._running = False

    def run_forever(self) -> None:
        """Blocking mode for `python main.py`."""
        self._stop.clear()
        try:
            self._run()
        except KeyboardInterrupt:
            if self.verbose:
                print("\nStopping.")
        finally:
            self._running = False

    def _run(self) -> None:
        sender: UdpSender | None = None
        self._running = True
        try:
            capture = AudioCapture(SAMPLE_RATE, CHUNK_SIZE)
            frame_seconds = CHUNK_SIZE / float(SAMPLE_RATE)

            features = AudioFeatureExtractor(
                sample_rate=SAMPLE_RATE,
                bass_range=(BASS_LOW_HZ, BASS_HIGH_HZ),
                mid_range=(MID_LOW_HZ, MID_HIGH_HZ),
                treble_range=(TREBLE_LOW_HZ, TREBLE_HIGH_HZ),
                gain_bass=0,
                gain_mid=0,
                gain_treble=0,
                gain_loudness=0,
                attack=0,
                release=0,
                beat_threshold_multiplier=0,
                beat_min_delta=0,
                beat_min_intensity=0,
                beat_baseline_alpha=0,
                beat_cooldown_frames=0,
            )

            lighting = LightingEngine(
                mode="bands",
                color_flow_speed=0,
                frame_seconds=frame_seconds,
                color_attack=0,
                color_release=0,
                color_deadzone=0,
                loudness_floor=0,
                flow_brightness_ceiling=0.5,
                beat_flash_intensity=0,
                beat_flash_decay=0.5,
            )

            sender = UdpSender(ESP32_IP, UDP_PORT)
            settings = apply_pipeline_settings(
                features, lighting, sender, frame_seconds
            )
            last_mtime = settings_mtime_ns()

            if self.verbose:
                print(
                    f"Sending RGB to {settings['ESP32_IP']}:{settings['UDP_PORT']}  "
                    f"mode={settings['LIGHTING_MODE']}"
                )
                print("Press Ctrl+C to stop.")

            for audio_chunk in capture.chunks():
                if self._stop.is_set():
                    break

                mtime = settings_mtime_ns()
                if mtime != last_mtime:
                    settings = apply_pipeline_settings(
                        features, lighting, sender, frame_seconds
                    )
                    last_mtime = mtime
                    if self.verbose:
                        print(
                            f"\nsettings reloaded  mode={settings['LIGHTING_MODE']}  "
                            f"flow={settings['COLOR_FLOW_SPEED']}  "
                            f"flash={settings['BEAT_FLASH_INTENSITY']}"
                        )

                frame = features.get_features(audio_chunk)
                rgb = lighting.get_rgb(frame)
                sender.send_rgb(rgb.red, rgb.green, rgb.blue)

                with self._lock:
                    self._last_rgb = (rgb.red, rgb.green, rgb.blue)
                    self._last_beat = frame.beat

                if self.verbose:
                    beat_marker = " BEAT" if frame.beat else "     "
                    print(
                        f"\rRGB {rgb.red:3d},{rgb.green:3d},{rgb.blue:3d} "
                        f"{beat_marker} "
                        f"(bass {frame.bass:3d} mid {frame.mid:3d} "
                        f"treb {frame.treble:3d} loud {frame.loudness:3d})",
                        end="",
                    )
        except Exception as exc:  # noqa: BLE001 - surface to dashboard status
            self._error = str(exc)
            if self.verbose:
                print(f"\nAudio runtime error: {exc}")
        finally:
            if sender is not None:
                try:
                    sender.send_rgb(0, 0, 0)
                    sender.close()
                except OSError:
                    pass
            self._running = False


# Shared instance for the dashboard process.
shared_runtime = AudioRuntime(verbose=True)
