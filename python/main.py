"""Process entrypoint: WASAPI capture -> features -> RGB -> UDP.

The realtime loop is intentionally thin. Signal analysis, lighting behavior,
and transport each live in their own modules so they can be tuned independently.
"""

from audio_capture import AudioCapture
from audio_features import AudioFeatureExtractor
from config import (
    ATTACK,
    BASS_HIGH_HZ,
    BASS_LOW_HZ,
    BEAT_BASELINE_ALPHA,
    BEAT_COOLDOWN_FRAMES,
    BEAT_FLASH_DECAY,
    BEAT_FLASH_INTENSITY,
    BEAT_MIN_DELTA,
    BEAT_MIN_INTENSITY,
    BEAT_THRESHOLD_MULTIPLIER,
    CHUNK_SIZE,
    COLOR_ATTACK,
    COLOR_DEADZONE,
    COLOR_RELEASE,
    ESP32_IP,
    GAIN_BASS,
    GAIN_LOUDNESS,
    GAIN_MID,
    GAIN_TREBLE,
    LOUDNESS_FLOOR,
    MID_HIGH_HZ,
    MID_LOW_HZ,
    RELEASE,
    SAMPLE_RATE,
    TREBLE_HIGH_HZ,
    TREBLE_LOW_HZ,
    UDP_PORT,
)
from lighting_engine import LightingEngine
from udp_sender import UdpSender


def main() -> None:
    capture = AudioCapture(SAMPLE_RATE, CHUNK_SIZE)

    features = AudioFeatureExtractor(
        sample_rate=SAMPLE_RATE,
        bass_range=(BASS_LOW_HZ, BASS_HIGH_HZ),
        mid_range=(MID_LOW_HZ, MID_HIGH_HZ),
        treble_range=(TREBLE_LOW_HZ, TREBLE_HIGH_HZ),
        gain_bass=GAIN_BASS,
        gain_mid=GAIN_MID,
        gain_treble=GAIN_TREBLE,
        gain_loudness=GAIN_LOUDNESS,
        attack=ATTACK,
        release=RELEASE,
        beat_threshold_multiplier=BEAT_THRESHOLD_MULTIPLIER,
        beat_min_delta=BEAT_MIN_DELTA,
        beat_min_intensity=BEAT_MIN_INTENSITY,
        beat_baseline_alpha=BEAT_BASELINE_ALPHA,
        beat_cooldown_frames=BEAT_COOLDOWN_FRAMES,
    )

    lighting = LightingEngine(
        color_attack=COLOR_ATTACK,
        color_release=COLOR_RELEASE,
        color_deadzone=COLOR_DEADZONE,
        loudness_floor=LOUDNESS_FLOOR,
        beat_flash_intensity=BEAT_FLASH_INTENSITY,
        beat_flash_decay=BEAT_FLASH_DECAY,
    )

    sender = UdpSender(ESP32_IP, UDP_PORT)

    print(f"Sending RGB to {ESP32_IP}:{UDP_PORT}")
    print("Press Ctrl+C to stop.")

    try:
        for audio_chunk in capture.chunks():
            frame = features.get_features(audio_chunk)
            rgb = lighting.get_rgb(frame)
            sender.send_rgb(rgb.red, rgb.green, rgb.blue)
            beat_marker = " BEAT" if frame.beat else "     "
            print(
                f"\rRGB {rgb.red:3d},{rgb.green:3d},{rgb.blue:3d} "
                f"{beat_marker} "
                f"(bass {frame.bass:3d} mid {frame.mid:3d} "
                f"treb {frame.treble:3d} loud {frame.loudness:3d})",
                end="",
            )
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        # Guarantee blackout even if capture/send raises mid-frame.
        sender.send_rgb(0, 0, 0)
        sender.close()


if __name__ == "__main__":
    main()
