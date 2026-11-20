# ESP32 LED Music Sync

This project drives a common-cathode RGB LED from audio playing on a Windows computer. Python analyzes bass, mids, treble, loudness, and bass onsets, then sends RGB values over UDP to an ESP32.

## Hardware

- ESP32
- Common-cathode RGB LED
- Red pin: GPIO 21
- Green pin: GPIO 22
- Blue pin: GPIO 23
- One 220-330 ohm resistor per color channel
- Common cathode connected to GND

## How It Works

1. Windows Python captures system audio with WASAPI loopback.
2. Audio is split into bass (40-150 Hz), mids (150-2000 Hz), treble (2000-10000 Hz), and full-band loudness.
3. Bass onset detection watches for sudden bass increases relative to the recent baseline.
4. Lighting mode chooses base color:
   - `bands`: bass -> red, mids -> green, treble -> blue
   - `flow`: hue slowly cycles through colors; loudness + beat still apply
5. Beat events add a short white flash overlay for sharper head-nod pulses.
6. UDP packets like `120,45,200` go to the ESP32.
7. ESP32 parses RGB and drives PWM on GPIO 21/22/23.

## Dev Workflow

- **Arduino IDE** = flash firmware to the ESP32
- **ESP32** = receive UDP RGB and drive the LED
- **Cursor + Python** = audio capture, feature extraction, beat detection, lighting

Re-flash the ESP32 when firmware changes. Python-only tuning in `config.py` does not require a re-flash.

## Setup

### 1. Install Python dependencies

```powershell
cd "c:\Users\vihoh\Coding Projects\ESP32-LED-Music-Sync"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create Wi-Fi secrets for the ESP32

```powershell
cd firmware\esp32_bass_led\LEDC_PWM
Copy-Item secrets.h.example secrets.h
```

Edit `firmware/esp32_bass_led/LEDC_PWM/secrets.h` with your Wi-Fi credentials.

### 3. Flash the ESP32

Open `firmware/esp32_bass_led/LEDC_PWM/LEDC_PWM.ino` in Arduino IDE, upload, then copy the IP from Serial Monitor (115200 baud).

### 4. Set ESP32 IP in `python/config.py`

```python
ESP32_IP = "your.esp.ip.here"
```

### 5. Run

```powershell
cd python
python main.py
```

When beat detection triggers, the terminal prints `BEAT` next to the RGB values.

### Optional: UDP RGB test (no audio)

```powershell
cd tests
python udp_test.py
```

## UDP Packet Format

- **Current:** `red,green,blue` (example: `80,120,200`)
- Legacy single integer still works on the ESP32 for quick tests (`128`).

## Tuning (`python/config.py`)

| Setting | Purpose |
|--------|---------|
| `LIGHTING_MODE` | `"bands"` or `"flow"` |
| `COLOR_FLOW_SPEED` | Hue degrees/second in flow mode |
| `FLOW_BRIGHTNESS_CEILING` | Caps flow baseline brightness so beat boosts stay on-hue |
| `GAIN_BASS`, `GAIN_MID`, `GAIN_TREBLE`, `GAIN_LOUDNESS` | Per-band sensitivity |
| `ATTACK` / `RELEASE` | Band energy smoothing |
| `BEAT_THRESHOLD_MULTIPLIER` | How much bass must jump relative to baseline |
| `BEAT_MIN_DELTA` | Minimum bass jump required for a beat |
| `BEAT_MIN_INTENSITY` | Ignore beat detection below this bass intensity |
| `BEAT_COOLDOWN_FRAMES` | Minimum spacing between beat flashes |
| `COLOR_ATTACK` / `COLOR_RELEASE` | Final RGB transition smoothness |
| `COLOR_DEADZONE` | Ignore tiny RGB flicker |
| `BEAT_FLASH_INTENSITY` | On-hue brightness boost (`1 + intensity/100`) |
| `BEAT_FLASH_DECAY` | How quickly the flash fades |
| `LOUDNESS_FLOOR` | Minimum brightness when the track is quiet |

Switch modes in `python/config.py`:

```python
LIGHTING_MODE = "flow"   # or "bands"
COLOR_FLOW_SPEED = 40.0  # higher = faster rainbow cycle
```

For sharper jumps, lower `ATTACK` and `COLOR_ATTACK`, or raise `BEAT_FLASH_INTENSITY`.

If too many false beats trigger, raise `BEAT_MIN_DELTA` or `BEAT_THRESHOLD_MULTIPLIER`.
If beats are missed, lower `BEAT_MIN_DELTA` or `BEAT_MIN_INTENSITY`.

## Quick Checklist

- ESP32 and PC on the same Wi-Fi
- Firmware re-flashed after RGB packet change
- `ESP32_IP` matches Serial Monitor
- Music plays through default Windows speaker

## Future Improvements
- Detect kicks/snares/claps better (right now it only detects bass changes)