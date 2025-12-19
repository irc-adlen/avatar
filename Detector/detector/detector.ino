#include <WiFi.h>
#include <PubSubClient.h>

// Pins HC-SR04
const int trigPin = 5;
const int echoPin = 4;

// Variables distance
long duration;
int distance;

// WiFi
const char* ssid = "iPhone de clem";
const char* password = "motdepasse";

// MQTT
const char* mqtt_server = "172.20.10.11";
const int mqtt_port = 1883;
const char* mqtt_topic = "stt/start";

WiFiClient espClient;
PubSubClient client(espClient);

// Connexion WiFi
void setup_wifi() {
  delay(10);
  Serial.print("Connexion WiFi");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connecté");
}

// Reconnexion MQTT
void reconnect_mqtt() {
  while (!client.connected()) {
    Serial.print("Connexion MQTT...");
    if (client.connect("ESP32C6_HCSR04")) {
      Serial.println("OK");
    } else {
      Serial.print("Échec, rc=");
      Serial.print(client.state());
      delay(2000);
    }
  }
}

void setup() {
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  Serial.begin(115200);

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect_mqtt();
  }
  client.loop();

  // Mesure distance
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH, 30000); // timeout 30 ms

  if (duration > 0) {
    distance = duration * 0.034 / 2;

    Serial.print("Distance: ");
    Serial.print(distance);
    Serial.println(" cm");

    // Envoi MQTT si distance < 100 cm
    if (distance < 100) {
      char msg[50];
      sprintf(msg, "Distance inferieure a 100 cm : %d cm", distance);

      client.publish(mqtt_topic, msg);
      Serial.println("Message MQTT envoyé");
    }
  } else {
    Serial.println("Aucune mesure");
  }

  delay(500);
}
