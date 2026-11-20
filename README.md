# ESP32 LED Music Sync

This project drives a common-cathode RGB LED from audio playing on a Windows computer. Python analyzes bass, mids, treble, and overall loudness, then sends RGB values over UDP to an ESP32.

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
3. Features map to RGB: bass -> red, mids -> green, treble -> blue; loudness scales overall brightness.
4. UDP packets like `120,45,200` go to the ESP32.
5. ESP32 parses RGB and drives PWM on GPIO 21/22/23.

## Dev Workflow

- **Arduino IDE** = flash firmware to the ESP32
- **ESP32** = receive UDP RGB and drive the LED
- **Cursor + Python** = audio capture, feature extraction, lighting

Re-flash the ESP32 when firmware changes (for example after switching to RGB packets).  
Python-only tuning in `config.py` does not require a re-flash.

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
| `GAIN_BASS`, `GAIN_MID`, `GAIN_TREBLE`, `GAIN_LOUDNESS` | Per-band sensitivity |
| `ATTACK` / `RELEASE` | Band energy smoothing |
| `COLOR_ATTACK` / `COLOR_RELEASE` | Final RGB transition smoothness |
| `COLOR_DEADZONE` | Ignore tiny RGB flicker |
| `LOUDNESS_FLOOR` | Minimum brightness when the track is quiet |

## Quick Checklist

- ESP32 and PC on the same Wi-Fi
- Firmware re-flashed after RGB packet change
- `ESP32_IP` matches Serial Monitor
- Music plays through default Windows speaker