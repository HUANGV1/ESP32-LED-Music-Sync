/*
 * ESP32 LED UDP sink
 *
 * Receives ASCII RGB frames from the host over Wi-Fi and drives a
 * common-cathode RGB LED via LEDC PWM (ESP32 Arduino core 3.x).
 *
 * Packet formats:
 *   "R,G,B"  preferred  e.g. "80,120,200"
 *   "N"      legacy     single intensity; mapped to R=N, G=N/3, B=N
 *
 * Pins: R=21, G=22, B=23. Credentials: secrets.h (gitignored).
 */

#include <WiFi.h>
#include <WiFiUdp.h>
#include "secrets.h"

const int RED_PIN = 21;
const int GREEN_PIN = 22;
const int BLUE_PIN = 23;

const unsigned int UDP_PORT = 4210;
// Host stopped sending (crash / Ctrl+C) — blank the LED instead of freezing.
const unsigned long PACKET_TIMEOUT_MS = 750;

WiFiUDP udp;

int redValue = 0;
int greenValue = 0;
int blueValue = 0;
unsigned long lastPacketTime = 0;

void setRgb(int red, int green, int blue) {
    ledcWrite(RED_PIN, constrain(red, 0, 255));
    ledcWrite(GREEN_PIN, constrain(green, 0, 255));
    ledcWrite(BLUE_PIN, constrain(blue, 0, 255));
}

void connectToWifi() {
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    Serial.print("Connecting to Wi-Fi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println();
    Serial.println("Connected!");
    Serial.print("ESP32 IP address: ");
    Serial.println(WiFi.localIP());
}

void setup() {
    Serial.begin(115200);
    delay(250);

    // 5 kHz / 8-bit: inaudible carrier, matches host 0–255 frames.
    ledcAttach(RED_PIN, 5000, 8);
    ledcAttach(GREEN_PIN, 5000, 8);
    ledcAttach(BLUE_PIN, 5000, 8);
    setRgb(0, 0, 0);

    connectToWifi();
    udp.begin(UDP_PORT);

    Serial.print("Listening for UDP packets on port ");
    Serial.println(UDP_PORT);
}

void loop() {
    int packetSize = udp.parsePacket();

    if (packetSize > 0) {
        char buffer[32];
        int length = udp.read(buffer, sizeof(buffer) - 1);
        buffer[length] = '\0';

        int parsedRed = 0;
        int parsedGreen = 0;
        int parsedBlue = 0;

        if (sscanf(buffer, "%d,%d,%d", &parsedRed, &parsedGreen, &parsedBlue) == 3) {
            redValue = constrain(parsedRed, 0, 255);
            greenValue = constrain(parsedGreen, 0, 255);
            blueValue = constrain(parsedBlue, 0, 255);
        } else {
            // Back-compat for pre-RGB host / quick intensity tests.
            int legacy = constrain(atoi(buffer), 0, 255);
            redValue = legacy;
            greenValue = legacy / 3;
            blueValue = legacy;
        }

        lastPacketTime = millis();

        Serial.print("RGB ");
        Serial.print(redValue);
        Serial.print(",");
        Serial.print(greenValue);
        Serial.print(",");
        Serial.println(blueValue);
    }

    if (millis() - lastPacketTime > PACKET_TIMEOUT_MS) {
        redValue = 0;
        greenValue = 0;
        blueValue = 0;
    }

    setRgb(redValue, greenValue, blueValue);
}
