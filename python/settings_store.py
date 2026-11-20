"""Persistent runtime settings for the LED sync pipeline.

Defaults live in `config.py`. Optional overrides are stored in
`settings.local.json` beside this module (gitignored). The dashboard writes
that file; `main.py` can reload it while running. Editing `config.py` still
works when the JSON file is absent.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SETTINGS_PATH = Path(__file__).with_name("settings.local.json")

# Schema drives the web dashboard (labels, ranges, groups, live vs restart).
SETTING_SPECS: dict[str, dict[str, Any]] = {
    "ESP32_IP": {
        "type": "string",
        "group": "Network",
        "label": "ESP32 IP",
        "live": False,
    },
    "UDP_PORT": {
        "type": "int",
        "group": "Network",
        "label": "UDP port",
        "min": 1024,
        "max": 65535,
        "step": 1,
        "live": False,
    },
    "GAIN_BASS": {
        "type": "float",
        "group": "Band gains",
        "label": "Bass gain",
        "min": 2.0,
        "max": 30.0,
        "step": 0.5,
        "live": True,
    },
    "GAIN_MID": {
        "type": "float",
        "group": "Band gains",
        "label": "Mid gain",
        "min": 2.0,
        "max": 30.0,
        "step": 0.5,
        "live": True,
    },
    "GAIN_TREBLE": {
        "type": "float",
        "group": "Band gains",
        "label": "Treble gain",
        "min": 2.0,
        "max": 30.0,
        "step": 0.5,
        "live": True,
    },
    "GAIN_LOUDNESS": {
        "type": "float",
        "group": "Band gains",
        "label": "Loudness gain",
        "min": 2.0,
        "max": 20.0,
        "step": 0.5,
        "live": True,
    },
    "ATTACK": {
        "type": "float",
        "group": "Envelopes",
        "label": "Attack",
        "min": 0.0,
        "max": 0.95,
        "step": 0.01,
        "live": True,
    },
    "RELEASE": {
        "type": "float",
        "group": "Envelopes",
        "label": "Release",
        "min": 0.0,
        "max": 0.98,
        "step": 0.01,
        "live": True,
    },
    "BEAT_THRESHOLD_MULTIPLIER": {
        "type": "float",
        "group": "Beat detection",
        "label": "Threshold multiplier",
        "min": 1.05,
        "max": 2.0,
        "step": 0.01,
        "live": True,
    },
    "BEAT_MIN_DELTA": {
        "type": "int",
        "group": "Beat detection",
        "label": "Min delta",
        "min": 4,
        "max": 60,
        "step": 1,
        "live": True,
    },
    "BEAT_MIN_INTENSITY": {
        "type": "int",
        "group": "Beat detection",
        "label": "Min intensity",
        "min": 0,
        "max": 120,
        "step": 1,
        "live": True,
    },
    "BEAT_BASELINE_ALPHA": {
        "type": "float",
        "group": "Beat detection",
        "label": "Baseline alpha",
        "min": 0.70,
        "max": 0.99,
        "step": 0.01,
        "live": True,
    },
    "BEAT_COOLDOWN_FRAMES": {
        "type": "int",
        "group": "Beat detection",
        "label": "Cooldown frames",
        "min": 1,
        "max": 12,
        "step": 1,
        "live": True,
    },
    "LIGHTING_MODE": {
        "type": "enum",
        "group": "Lighting",
        "label": "Mode",
        "options": ["bands", "flow"],
        "live": True,
    },
    "COLOR_FLOW_SPEED": {
        "type": "float",
        "group": "Lighting",
        "label": "Flow speed (°/s)",
        "min": 5.0,
        "max": 180.0,
        "step": 1.0,
        "live": True,
    },
    "FLOW_BRIGHTNESS_CEILING": {
        "type": "float",
        "group": "Lighting",
        "label": "Flow brightness ceiling",
        "min": 0.20,
        "max": 1.0,
        "step": 0.01,
        "live": True,
    },
    "COLOR_ATTACK": {
        "type": "float",
        "group": "Display RGB",
        "label": "Color attack",
        "min": 0.0,
        "max": 0.95,
        "step": 0.01,
        "live": True,
    },
    "COLOR_RELEASE": {
        "type": "float",
        "group": "Display RGB",
        "label": "Color release",
        "min": 0.0,
        "max": 0.98,
        "step": 0.01,
        "live": True,
    },
    "COLOR_DEADZONE": {
        "type": "int",
        "group": "Display RGB",
        "label": "Color deadzone",
        "min": 0,
        "max": 15,
        "step": 1,
        "live": True,
    },
    "LOUDNESS_FLOOR": {
        "type": "float",
        "group": "Display RGB",
        "label": "Loudness floor",
        "min": 0.0,
        "max": 0.50,
        "step": 0.01,
        "live": True,
    },
    "BEAT_FLASH_INTENSITY": {
        "type": "int",
        "group": "Display RGB",
        "label": "Beat flash intensity",
        "min": 0,
        "max": 200,
        "step": 1,
        "live": True,
    },
    "BEAT_FLASH_DECAY": {
        "type": "float",
        "group": "Display RGB",
        "label": "Beat flash decay",
        "min": 0.20,
        "max": 0.90,
        "step": 0.01,
        "live": True,
    },
}


def defaults_from_config() -> dict[str, Any]:
    import config as cfg

    return {key: getattr(cfg, key) for key in SETTING_SPECS if hasattr(cfg, key)}


def _coerce_value(key: str, value: Any) -> Any:
    spec = SETTING_SPECS[key]
    kind = spec["type"]

    if kind == "string":
        return str(value)

    if kind == "enum":
        val = str(value).lower().strip()
        if val not in spec["options"]:
            raise ValueError(f"{key}: must be one of {spec['options']}")
        return val

    if kind == "int":
        val = int(round(float(value)))
        val = max(spec["min"], min(spec["max"], val))
        return val

    if kind == "float":
        val = float(value)
        val = max(spec["min"], min(spec["max"], val))
        return val

    raise ValueError(f"Unknown spec type for {key}")


def merged_settings() -> dict[str, Any]:
    values = defaults_from_config()
    if SETTINGS_PATH.exists():
        with SETTINGS_PATH.open(encoding="utf-8") as handle:
            overrides = json.load(handle)
        for key, value in overrides.items():
            if key in SETTING_SPECS:
                values[key] = _coerce_value(key, value)
    return values


def save_settings(partial: dict[str, Any]) -> dict[str, Any]:
    current = merged_settings()
    for key, value in partial.items():
        if key not in SETTING_SPECS:
            continue
        current[key] = _coerce_value(key, value)

    overrides = {k: current[k] for k in SETTING_SPECS}
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(overrides, handle, indent=2, sort_keys=True)
        handle.write("\n")

    return current


def apply_overrides_to_config_module() -> None:
    """Optional: merge JSON into config module globals at import time."""
    if not SETTINGS_PATH.exists():
        return
    import config as cfg

    merged = merged_settings()
    for key, value in merged.items():
        setattr(cfg, key, value)


def settings_mtime_ns() -> int | None:
    if not SETTINGS_PATH.exists():
        return None
    return SETTINGS_PATH.stat().st_mtime_ns