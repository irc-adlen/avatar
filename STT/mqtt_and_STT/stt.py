import subprocess
import logging
import paho.mqtt.client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883
MQTT_TOPIC = "stt/start"
PROJECT_PATH = "/home/avatar/output"
WHISPER_CONTAINER_PATH = "/opt/whisper.cpp/output"
logger = logging.getLogger(__name__)


def run_stt():
    """
    Launch whisper.cpp Docker container and return the transcribed text
    """
    logger.info("Starting STT process")

    cmd = [
        "docker", "run", "--rm",
        "--gpus", "all",
        "--device", "/dev/snd",
        "-v", f"{PROJECT_PATH}:{WHISPER_CONTAINER_PATH}",
        "whisper-mic-gpu",
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    output, _ = process.communicate()
    return output


def on_message(client, userdata, msg):
    logger.info("MQTT trigger received")

    text = run_stt()
    logger.info(f"STT result: {text}")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(MQTT_TOPIC)

    logger.info("Waiting for MQTT trigger...")
    client.loop_forever()


if __name__ == "__main__":
    main()
