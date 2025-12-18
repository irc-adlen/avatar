import subprocess
import logging
import threading
import time
import paho.mqtt.client as mqtt
from voice_recorder import start_recording
from whisperv3 import transcribe_audio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883
MQTT_TOPIC = "stt/start"

PROJECT_PATH = "/home/avatar/output"
WHISPER_CONTAINER_PATH = "/opt/whisper.cpp/output"
WHISPER_CONTAINER_NAME = "whisper_stt_container"

logger = logging.getLogger(__name__)

def run_stt_with_timeout():
    record_path = start_recording()
    print("Recording saved at:", record_path)
    print("Starting transcription...")
    transcribe_audio(record_path)

def on_message(client, userdata, msg):
    logger.info("MQTT trigger received")
    run_stt_with_timeout()


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(MQTT_TOPIC)

    logger.info("Waiting for MQTT trigger...")
    client.loop_forever()


if __name__ == "__main__":
    main()
