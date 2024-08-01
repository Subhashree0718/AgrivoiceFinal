#include <Arduino.h>
#include <WiFi.h>
#include <ESPmDNS.h>
#include <WebServer.h>
#include <Firebase_ESP_Client.h>

// Firebase credentials
#define WIFI_SSID "REPLACE_WITH_YOUR_SSID"
#define WIFI_PASSWORD "REPLACE_WITH_YOUR_PASSWORD"
#define API_KEY "REPLACE_WITH_YOUR_FIREBASE_PROJECT_API_KEY"
#define DATABASE_URL "REPLACE_WITH_YOUR_FIREBASE_DATABASE_URL"

FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

unsigned long sendDataPrevMillis = 0;
int count = 0;
bool signupOK = false;

WebServer server(80);
String webSite = "";
String contact = "";
String website = "";
String budget = "";

const int a1 = 33;
const int a2 = 32;
const int a3 = 35;

int pot1 = 0;
int pot2 = 0;
int pot3 = 0;

String status = "";

#define MOISTURE_SENSOR_PIN 34 // Analog pin connected to the sensor

void setup() {
  Serial.begin(115200); // Initialize serial communication
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(300);
  }

  if (MDNS.begin("esp32")) {
    Serial.println("MDNS responder started");
  }
  Serial.println();
  Serial.print("Connected with IP: ");
  Serial.println(WiFi.localIP());
  Serial.println();

  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;

  if (Firebase.signUp(&config, &auth, "", "")) {
    Serial.println("Firebase sign up successful");
    signupOK = true;
  } else {
    Serial.printf("%s\n", config.signer.signupError.message.c_str());
  }

  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
}

void loop() {
  int sensorValue = analogRead(MOISTURE_SENSOR_PIN); // Read the sensor value
  Serial.print("Soil Moisture Value: ");
  Serial.println(sensorValue); // Print the value to the Serial Monitor

  pot1 = analogRead(a1);
  pot2 = analogRead(a2);
  pot3 = analogRead(a3);

  if (pot1 <= 800 && pot2 <= 800 && pot3 > 2600) {
    status = "Best to plant Potatoes, Carrots, Sweet Potatoes, Turnips";
  } else if (pot1 <= 1200 && pot2 <= 800 && pot3 > 2600) {
    status = "Best to plant Spinach, Lettuce, Swiss Chard, Kale and Mustard";
  } else if (pot1 > 1200 && pot2 > 800 && pot3 <= 2600) {
    status = "Best to plant Corn, Wheat, Barley, Oats";
  } else {
    status = "Best to plant Banana, Papaya, Cucumber, Tomatoes.";
  }

  Serial.println(status);

  delay(1000); // Wait for 1 second before the next reading

  if (Firebase.ready() && signupOK && (millis() - sendDataPrevMillis > 500 || sendDataPrevMillis == 0)) {
    sendDataPrevMillis = millis();

    // Firebase RTDB write
    if (Firebase.RTDB.setInt(&fbdo, "soilMoisture", sensorValue) &&
        Firebase.RTDB.setInt(&fbdo, "nitrous", pot1) &&
        Firebase.RTDB.setInt(&fbdo, "phosporous", pot2) &&
        Firebase.RTDB.setInt(&fbdo, "potassium", pot3)
        Firebase.RTDB.setInt(&fbdo, "CROP", status)) {
      Serial.println("Data uploaded successfully");
    } else {
      Serial.println("Failed to upload data");
      Serial.println("REASON: " + fbdo.errorReason());
    }
    count++;
  }
}
