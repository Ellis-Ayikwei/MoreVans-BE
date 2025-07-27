/**
 * Waste Wise - Smart Waste Bin Sensor
 * ESP32 Firmware for IoT Waste Management System
 * 
 * Features:
 * - Ultrasonic sensor for fill level measurement
 * - Temperature and humidity monitoring
 * - MQTT communication
 * - Deep sleep for power saving
 * - OTA updates
 * - Battery monitoring
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <ArduinoOTA.h>
#include <Preferences.h>

// Pin Definitions
#define TRIG_PIN 5
#define ECHO_PIN 18
#define DHT_PIN 4
#define BATTERY_PIN 35
#define LED_PIN 2

// Sensor Configuration
#define DHT_TYPE DHT22
#define BIN_HEIGHT 100.0  // Bin height in cm
#define MEASUREMENT_INTERVAL 300000  // 5 minutes in milliseconds
#define DEEP_SLEEP_TIME 300  // 5 minutes in seconds

// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT Configuration
const char* mqtt_server = "YOUR_MQTT_SERVER";
const int mqtt_port = 1883;
const char* mqtt_user = "";
const char* mqtt_password = "";

// Device Configuration
String device_id = "BIN_";
String sensor_topic = "waste-wise/sensors/";
String command_topic = "waste-wise/commands/";
String alert_topic = "waste-wise/alerts";

// Global Objects
WiFiClient espClient;
PubSubClient mqtt(espClient);
DHT dht(DHT_PIN, DHT_TYPE);
Preferences preferences;

// Variables
float empty_distance = 0;
float full_distance = 0;
unsigned long lastMeasurement = 0;
int failedReadings = 0;
const int MAX_FAILED_READINGS = 5;

// Function Prototypes
void setup_wifi();
void mqtt_callback(char* topic, byte* payload, unsigned int length);
void reconnect_mqtt();
float measure_distance();
float calculate_fill_level(float distance);
float read_battery_level();
void send_sensor_data();
void handle_command(JsonDocument& doc);
void calibrate_sensor();
void enter_deep_sleep();
void setup_ota();

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  // Initialize preferences
  preferences.begin("waste-bin", false);
  
  // Load calibration data
  empty_distance = preferences.getFloat("empty_dist", BIN_HEIGHT);
  full_distance = preferences.getFloat("full_dist", 10.0);
  
  // Generate unique device ID
  uint64_t chipid = ESP.getEfuseMac();
  device_id += String((uint32_t)chipid, HEX);
  sensor_topic += device_id + "/data";
  command_topic += device_id;
  
  Serial.println("Waste Wise Sensor Starting...");
  Serial.println("Device ID: " + device_id);
  
  // Initialize sensors
  dht.begin();
  
  // Connect to WiFi
  setup_wifi();
  
  // Setup MQTT
  mqtt.setServer(mqtt_server, mqtt_port);
  mqtt.setCallback(mqtt_callback);
  
  // Setup OTA
  setup_ota();
  
  // Connect to MQTT
  reconnect_mqtt();
  
  // Send initial reading
  send_sensor_data();
}

void loop() {
  // Handle OTA updates
  ArduinoOTA.handle();
  
  // Maintain MQTT connection
  if (!mqtt.connected()) {
    reconnect_mqtt();
  }
  mqtt.loop();
  
  // Check if it's time for a measurement
  unsigned long currentMillis = millis();
  if (currentMillis - lastMeasurement >= MEASUREMENT_INTERVAL) {
    lastMeasurement = currentMillis;
    send_sensor_data();
    
    // Enter deep sleep if battery is low
    float battery = read_battery_level();
    if (battery < 20.0) {
      Serial.println("Low battery - entering deep sleep");
      enter_deep_sleep();
    }
  }
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    attempts++;
  }
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Failed to connect to WiFi - entering deep sleep");
    enter_deep_sleep();
  }
  
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  digitalWrite(LED_PIN, HIGH);
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  
  // Parse JSON payload
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, payload, length);
  
  if (error) {
    Serial.print("JSON parsing failed: ");
    Serial.println(error.c_str());
    return;
  }
  
  // Handle command
  handle_command(doc);
}

void reconnect_mqtt() {
  int attempts = 0;
  while (!mqtt.connected() && attempts < 5) {
    Serial.print("Attempting MQTT connection...");
    
    if (mqtt.connect(device_id.c_str(), mqtt_user, mqtt_password)) {
      Serial.println("connected");
      
      // Subscribe to command topic
      mqtt.subscribe(command_topic.c_str());
      Serial.println("Subscribed to: " + command_topic);
      
      // Flash LED to indicate connection
      for (int i = 0; i < 3; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(100);
        digitalWrite(LED_PIN, LOW);
        delay(100);
      }
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqtt.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
      attempts++;
    }
  }
  
  if (!mqtt.connected()) {
    Serial.println("Failed to connect to MQTT - entering deep sleep");
    enter_deep_sleep();
  }
}

float measure_distance() {
  // Clear the trigger pin
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  
  // Send ultrasonic pulse
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  // Read echo time
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);  // 30ms timeout
  
  if (duration == 0) {
    Serial.println("Ultrasonic sensor timeout");
    return -1;
  }
  
  // Calculate distance in cm
  float distance = duration * 0.034 / 2;
  
  // Validate reading
  if (distance < 2 || distance > 400) {
    Serial.println("Invalid distance reading");
    return -1;
  }
  
  return distance;
}

float calculate_fill_level(float distance) {
  if (distance < 0) return -1;
  
  // Calculate fill percentage
  float fill_percentage = 100.0 - ((distance - full_distance) / (empty_distance - full_distance) * 100.0);
  
  // Constrain to valid range
  fill_percentage = constrain(fill_percentage, 0, 100);
  
  return fill_percentage;
}

float read_battery_level() {
  // Read analog value
  int raw = analogRead(BATTERY_PIN);
  
  // Convert to voltage (assuming voltage divider)
  float voltage = (raw / 4095.0) * 3.3 * 2;  // Multiply by 2 for voltage divider
  
  // Convert to percentage (assuming 4.2V = 100%, 3.0V = 0%)
  float percentage = (voltage - 3.0) / (4.2 - 3.0) * 100.0;
  percentage = constrain(percentage, 0, 100);
  
  return percentage;
}

void send_sensor_data() {
  Serial.println("Taking sensor readings...");
  
  // Take multiple distance readings for accuracy
  float total_distance = 0;
  int valid_readings = 0;
  
  for (int i = 0; i < 5; i++) {
    float distance = measure_distance();
    if (distance > 0) {
      total_distance += distance;
      valid_readings++;
    }
    delay(50);
  }
  
  if (valid_readings == 0) {
    failedReadings++;
    Serial.println("All distance readings failed");
    
    if (failedReadings >= MAX_FAILED_READINGS) {
      // Send alert
      StaticJsonDocument<256> alert;
      alert["sensor_id"] = device_id;
      alert["alert_type"] = "sensor_malfunction";
      alert["message"] = "Ultrasonic sensor not responding";
      
      char buffer[256];
      serializeJson(alert, buffer);
      mqtt.publish(alert_topic.c_str(), buffer);
      
      // Enter deep sleep
      enter_deep_sleep();
    }
    return;
  }
  
  failedReadings = 0;
  float avg_distance = total_distance / valid_readings;
  float fill_level = calculate_fill_level(avg_distance);
  
  // Read other sensors
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  float battery = read_battery_level();
  
  // Prepare JSON payload
  StaticJsonDocument<512> doc;
  doc["sensor_id"] = device_id;
  doc["fill_level"] = round(fill_level);
  doc["distance"] = avg_distance;
  doc["battery_level"] = round(battery);
  doc["signal_strength"] = WiFi.RSSI();
  doc["timestamp"] = millis();
  
  if (!isnan(temperature)) {
    doc["temperature"] = temperature;
  }
  
  if (!isnan(humidity)) {
    doc["humidity"] = humidity;
  }
  
  // Serialize and publish
  char buffer[512];
  size_t len = serializeJson(doc, buffer);
  
  if (mqtt.publish(sensor_topic.c_str(), buffer, len)) {
    Serial.println("Data sent successfully");
    Serial.println(buffer);
    
    // Flash LED
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
  } else {
    Serial.println("Failed to send data");
  }
  
  // Check for alerts
  if (fill_level >= 80) {
    StaticJsonDocument<256> alert;
    alert["sensor_id"] = device_id;
    alert["alert_type"] = "high_fill";
    alert["fill_level"] = fill_level;
    alert["message"] = "Bin is " + String(fill_level) + "% full";
    
    char alertBuffer[256];
    serializeJson(alert, alertBuffer);
    mqtt.publish(alert_topic.c_str(), alertBuffer);
  }
  
  if (battery < 30) {
    StaticJsonDocument<256> alert;
    alert["sensor_id"] = device_id;
    alert["alert_type"] = "low_battery";
    alert["battery_level"] = battery;
    alert["message"] = "Battery level is " + String(battery) + "%";
    
    char alertBuffer[256];
    serializeJson(alert, alertBuffer);
    mqtt.publish(alert_topic.c_str(), alertBuffer);
  }
}

void handle_command(JsonDocument& doc) {
  String command = doc["command"];
  
  if (command == "calibrate") {
    calibrate_sensor();
  } else if (command == "read") {
    send_sensor_data();
  } else if (command == "restart") {
    ESP.restart();
  } else if (command == "sleep") {
    int duration = doc["parameters"]["duration"] | DEEP_SLEEP_TIME;
    esp_sleep_enable_timer_wakeup(duration * 1000000ULL);
    esp_deep_sleep_start();
  } else if (command == "set_interval") {
    int interval = doc["parameters"]["interval"];
    // Store new interval in preferences
    preferences.putInt("interval", interval);
  }
  
  // Send command response
  StaticJsonDocument<256> response;
  response["sensor_id"] = device_id;
  response["command"] = command;
  response["status"] = "completed";
  response["timestamp"] = millis();
  
  char buffer[256];
  serializeJson(response, buffer);
  
  String response_topic = "waste-wise/commands/" + device_id + "/response";
  mqtt.publish(response_topic.c_str(), buffer);
}

void calibrate_sensor() {
  Serial.println("Starting calibration...");
  
  // Calibrate empty distance
  Serial.println("Measuring empty bin distance...");
  float empty_total = 0;
  int valid = 0;
  
  for (int i = 0; i < 10; i++) {
    float distance = measure_distance();
    if (distance > 0) {
      empty_total += distance;
      valid++;
    }
    delay(100);
  }
  
  if (valid > 0) {
    empty_distance = empty_total / valid;
    preferences.putFloat("empty_dist", empty_distance);
    Serial.println("Empty distance: " + String(empty_distance) + " cm");
  }
  
  // For full distance, we'll use a default or wait for manual input
  full_distance = 10.0;  // 10cm from sensor when full
  preferences.putFloat("full_dist", full_distance);
  
  Serial.println("Calibration complete");
}

void enter_deep_sleep() {
  Serial.println("Entering deep sleep...");
  
  // Disconnect MQTT
  mqtt.disconnect();
  
  // Disconnect WiFi
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
  
  // Configure wake up timer
  esp_sleep_enable_timer_wakeup(DEEP_SLEEP_TIME * 1000000ULL);
  
  // Enter deep sleep
  esp_deep_sleep_start();
}

void setup_ota() {
  ArduinoOTA.setHostname(device_id.c_str());
  
  ArduinoOTA.onStart([]() {
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH) {
      type = "sketch";
    } else {
      type = "filesystem";
    }
    Serial.println("Start updating " + type);
  });
  
  ArduinoOTA.onEnd([]() {
    Serial.println("\nEnd");
  });
  
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });
  
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) {
      Serial.println("Auth Failed");
    } else if (error == OTA_BEGIN_ERROR) {
      Serial.println("Begin Failed");
    } else if (error == OTA_CONNECT_ERROR) {
      Serial.println("Connect Failed");
    } else if (error == OTA_RECEIVE_ERROR) {
      Serial.println("Receive Failed");
    } else if (error == OTA_END_ERROR) {
      Serial.println("End Failed");
    }
  });
  
  ArduinoOTA.begin();
}