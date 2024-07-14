#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);
String busData[2] = {"", ""};
String trainData[2] = {"", ""};
bool displayBus = true;
unsigned long previousMillis = 0;
const long interval = 5000; // interval at which to switch display (milliseconds)
bool dataReceived = false;

void setup() {
  Serial.begin(9600);
  lcd.begin(16, 2); // Initialize LCD: 16 columns, 2 rows
  lcd.clear();
  lcd.print("Waiting for");
  lcd.setCursor(0, 1);
  lcd.print("data...");
}

void loop() {
  if (Serial.available()) {
    dataReceived = true;
    lcd.clear();
    lcd.print("Receiving data");
    delay(1000);
    
    // Read bus data
    for (int i = 0; i < 2; i++) {
      if (Serial.available()) {
        busData[i] = Serial.readStringUntil('\n');
        busData[i].trim();
      }
    }
    
    // Read train data
    for (int i = 0; i < 2; i++) {
      if (Serial.available()) {
        trainData[i] = Serial.readStringUntil('\n');
        trainData[i].trim();
      }
    }
  }

  unsigned long currentMillis = millis();

  if (dataReceived) {
    if (currentMillis - previousMillis >= interval) {
      previousMillis = currentMillis;
      displayBus = !displayBus;
      lcd.clear();
      if (displayBus) {
        lcd.setCursor(0, 0);
        lcd.print(busData[0]);
        lcd.setCursor(0, 1);
        lcd.print(busData[1]);
      } else {
        lcd.setCursor(0, 0);
        lcd.print(trainData[0]);
        lcd.setCursor(0, 1);
        lcd.print(trainData[1]);
      }
    }
  } else {
    // If no data received, display waiting message
    lcd.setCursor(0, 0);
    lcd.print("Waiting for");
    lcd.setCursor(0, 1);
    lcd.print("data...");
  }
}
