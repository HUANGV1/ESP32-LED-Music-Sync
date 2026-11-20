# ESP32 LED Music Sync

This project makes a common-cathode RGB LED pulse with bass from audio playing on a Windows computer.

## Hardware

- ESP32
- Common-cathode RGB LED
- Red pin: GPIO 21
- Green pin: GPIO 22
- Blue pin: GPIO 23
- One 220-330 ohm resistor per color channel
- Common cathode connected to GND

## How It Works

1. The Windows Python app captures system audio with WASAPI loopback.
2. The app filters the audio down to bass frequencies.
3. Bass energy is converted into a brightness value from 0 to 255.
4. The value is sent to the ESP32 over UDP.
5. The ESP32 uses LEDC PWM to control the RGB LED.

## Dev Workflow

Cursor is used to edit code and run Python.  
Arduino IDE is used to compile and flash the ESP32.

- **Arduino IDE** = flash firmware to the ESP32
- **ESP32** = receive UDP brightness values and drive the LED
- **Cursor + Python** = capture PC audio, detect bass, send values over Wi-Fi

You only need to re-flash the ESP32 when firmware changes.  
Changing Python settings like `GAIN` does **not** require a re-flash.

You do **not** need to leave Arduino IDE open after uploading.  
The ESP32 keeps running from its flash memory. Close Serial Monitor before the next Upload if the COM port is busy.

## Setup

### 1. Install Python dependencies

In Cursor’s terminal (or PowerShell):

```powershell
cd "c:\Users\vihoh\Coding Projects\ESP32-LED-Music-Sync"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create Wi-Fi secrets for the ESP32

The sketch folder needs a private `secrets.h` file next to the `.ino`:

```powershell
cd firmware\esp32_bass_led\LEDC_PWM
Copy-Item secrets.h.example secrets.h
```

Edit `firmware/esp32_bass_led/LEDC_PWM/secrets.h` with your real Wi-Fi name and password.  
`secrets.h` is gitignored, so it will not be committed.

### 3. Flash the ESP32 with Arduino IDE

Files that matter for flashing:

- `firmware/esp32_bass_led/LEDC_PWM/LEDC_PWM.ino`
- `firmware/esp32_bass_led/LEDC_PWM/secrets.h`

Steps:

1. Open Arduino IDE.
2. Install the ESP32 board package if needed (`Boards Manager` → search `esp32` by Espressif).
3. Select your board (for example `ESP32 Dev Module`) and the correct COM port.
4. Open `firmware/esp32_bass_led/LEDC_PWM/LEDC_PWM.ino`.
5. Click **Upload**.
6. Open **Serial Monitor** at **115200** baud.
7. Copy the printed ESP32 IP address, for example `192.168.1.105`.

### 4. Set the ESP32 IP in Python config

Edit `python/config.py` and update:

```python
ESP32_IP = "192.168.1.105"
```

Replace that value with the IP shown in Arduino Serial Monitor.  
If you skip this step, Python will send packets to the wrong device and the LED will not respond.

Also confirm `UDP_PORT = 4210` matches the firmware.

### 5. Run the Python audio engine

```powershell
cd "c:\Users\vihoh\Coding Projects\ESP32-LED-Music-Sync"
.venv\Scripts\activate
cd python
python main.py
```

Play music on your PC. The terminal should show bass intensity values, and the LED should pulse.

Press `Ctrl+C` to stop.

## Tuning

Edit values in `python/config.py` (no re-flash needed):

- `GAIN`: higher = brighter / more sensitive
- `ATTACK`: lower = snappier rise on big bass hits
- `RELEASE`: higher = slower fade, less jumpy on small changes
- `INTENSITY_DEADZONE`: higher = ignore more tiny brightness flicker

If small fluctuations still look jumpy, try:

```python
RELEASE = 0.95
INTENSITY_DEADZONE = 6
```

## Quick Checklist

- ESP32 and PC are on the same Wi-Fi
- `secrets.h` has the correct Wi-Fi credentials
- `ESP32_IP` in `python/config.py` matches Serial Monitor
- Music is playing through your default Windows speaker
- Arduino IDE does not need to stay open while Python is running
