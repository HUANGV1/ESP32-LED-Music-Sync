const int RED_PIN = 21;
const int GREEN_PIN = 22;
const int BLUE_PIN = 23;

void setup() {
    ledcAttach(RED_PIN, 5000, 8);
    ledcAttach(GREEN_PIN, 5000, 8);
    ledcAttach(BLUE_PIN, 5000, 8);
}

void loop() {
    // Red
    ledcWrite(RED_PIN, 255);
    ledcWrite(GREEN_PIN, 0);
    ledcWrite(BLUE_PIN, 0);
    delay(1000);

    // Green
    ledcWrite(RED_PIN, 0);
    ledcWrite(GREEN_PIN, 255);
    ledcWrite(BLUE_PIN, 0);
    delay(1000);

    // Blue
    ledcWrite(RED_PIN, 0);
    ledcWrite(GREEN_PIN, 0);
    ledcWrite(BLUE_PIN, 255);
    delay(1000);

    // Off
    ledcWrite(RED_PIN, 0);
    ledcWrite(GREEN_PIN, 0);
    ledcWrite(BLUE_PIN, 0);
    delay(1000);
}