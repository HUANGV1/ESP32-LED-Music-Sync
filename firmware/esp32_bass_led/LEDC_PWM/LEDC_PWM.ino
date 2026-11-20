/*
 * ESP32 Bass LED Firmware
 * -----------------------
 * This program runs on the ESP32 microcontroller.
 *
 * What it does, step by step:
 *   1. Connects the ESP32 to your Wi-Fi network.
 *   2. Listens for small UDP network packets from your Windows PC.
 *   3. Each packet contains a bass intensity number from 0 to 255.
 *   4. Uses PWM (pulse-width modulation) to drive an RGB LED.
 *   5. Brighter bass = brighter LED.
 *
 * Hardware assumed:
 *   - Common-cathode RGB LED
 *   - Red   -> GPIO 21 (through a resistor)
 *   - Green -> GPIO 22 (through a resistor)
 *   - Blue  -> GPIO 23 (through a resistor)
 *   - Common cathode -> GND
 */

// Built-in Arduino libraries for Wi-Fi and UDP networking.
#include <WiFi.h>
#include <WiFiUdp.h>

// Private Wi-Fi credentials live in secrets.h (gitignored).
// Copy secrets.h.example -> secrets.h and fill in your values.
#include "secrets.h"


// ============================================================
// CONFIGURATION
// ============================================================

// GPIO pin numbers on the ESP32 that control each LED color.
const int RED_PIN = 21;
const int GREEN_PIN = 22;
const int BLUE_PIN = 23;

// UDP port number. Your Python program must send to this exact port.
const unsigned int UDP_PORT = 4210;

// If no packet arrives for this many milliseconds, turn the LED off.
// This prevents the LED from staying stuck bright if Python stops.
const unsigned long PACKET_TIMEOUT_MS = 750;


// ============================================================
// GLOBAL STATE
// ============================================================

// This object handles receiving UDP packets over Wi-Fi.
WiFiUDP udp;

// The latest bass intensity received from the computer.
// 0 = silence / no bass, 255 = very strong bass.
int bassIntensity = 0;

// Timestamp (in milliseconds since boot) of the last received packet.
// Used with PACKET_TIMEOUT_MS to detect a stalled computer.
unsigned long lastPacketTime = 0;


// ============================================================
// HELPER FUNCTIONS
// ============================================================

/*
 * setRgb()
 * Writes PWM duty-cycle values to the three LED pins.
 */
void setRgb(int red, int green, int blue) {
    // constrain() clamps the value into the legal PWM range 0..255.
    // ledcWrite(pin, duty) sets that pin's PWM brightness.
    ledcWrite(RED_PIN, constrain(red, 0, 255));
    ledcWrite(GREEN_PIN, constrain(green, 0, 255));
    ledcWrite(BLUE_PIN, constrain(blue, 0, 255));
}

/*
 * connectToWifi()
 */
void connectToWifi() {
    // WIFI_STA = Station mode (join an existing router), not AP mode.
    WiFi.mode(WIFI_STA);

    // Start the connection attempt using the credentials above.
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    Serial.print("Connecting to Wi-Fi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    // Once connected, print the IP address assigned by your router.
    // You must copy this IP into python/config.py as ESP32_IP.
    Serial.println();
    Serial.println("Connected!");
    Serial.print("ESP32 IP address: ");
    Serial.println(WiFi.localIP());
}


// ============================================================
// ARDUINO SETUP / LOOP
// ============================================================

/*
 * setup()
 * Runs once when the ESP32 boots or resets.
 * Use this for one-time initialization only.
 */
void setup() {
    // Open the USB serial console at 115200 baud so you can debug
    // in Arduino IDE -> Tools -> Serial Monitor.
    Serial.begin(115200);

    delay(250);

    /*
     * ledcAttach(pin, frequencyHz, resolutionBits)
     * This is the Arduino ESP32 core 3.x API.
     */
    ledcAttach(RED_PIN, 5000, 8);
    ledcAttach(GREEN_PIN, 5000, 8);
    ledcAttach(BLUE_PIN, 5000, 8);

    // Start with the LED fully off.
    setRgb(0, 0, 0);

    // Join Wi-Fi before listening for packets.
    connectToWifi();

    // Begin listening for UDP packets on UDP_PORT.
    udp.begin(UDP_PORT);

    Serial.print("Listening for UDP packets on port ");
    Serial.println(UDP_PORT);
}

/*
 * loop()
 * Runs over and over forever after setup() finishes.
 * Each pass:
 *   1. Check if a UDP packet arrived.
 *   2. If yes, parse the bass intensity number.
 *   3. If packets stop coming, fade intensity to 0.
 *   4. Update the LED color/brightness.
 */
void loop() {
    // parsePacket() returns how many bytes are waiting, or 0 if none.
    int packetSize = udp.parsePacket();

    // Only process a packet if at least one byte arrived.
    if (packetSize > 0) {
        // Temporary buffer to hold the incoming text, e.g. "128".
        // Size 16 is plenty for a small integer string.
        char buffer[16];

        // Read the packet bytes into buffer.
        // Leave 1 byte free at the end for the null terminator '\0'.
        int length = udp.read(buffer, sizeof(buffer) - 1);

        // C-strings need a terminating zero byte so atoi() knows
        // where the text ends.
        buffer[length] = '\0';

        // atoi() converts text like "128" into the integer 128.
        // constrain() then clamps it into 0..255 for PWM safety.
        bassIntensity = constrain(atoi(buffer), 0, 255);

        // Remember when this packet arrived (milliseconds since boot).
        lastPacketTime = millis();

        // Print the value so you can watch it in Serial Monitor.
        Serial.print("Bass intensity: ");
        Serial.println(bassIntensity);
    }

    // Fail-safe: if Python stops sending for too long, force LED off.
    // millis() wraps eventually, but the subtraction still works
    // correctly for timeouts of this size.
    if (millis() - lastPacketTime > PACKET_TIMEOUT_MS) {
        bassIntensity = 0;
    }

    /*
     * Map bass intensity into an RGB color.
     * Currently:
     *   - Red stays off
     *   - Blue follows bass directly
     *   - Green is a weaker copy of blue, so strong bass looks cyan-ish
     *
     * You can later change this mapping for different color moods.
     */
    int blue = bassIntensity;
    int green = bassIntensity / 3;

    // Push the new color values out to the LED pins via PWM.
    setRgb(0, green, blue);
}
