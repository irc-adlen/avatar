import subprocess
import logging
import threading
import time
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
WHISPER_CONTAINER_NAME = "whisper_stt_container"

logger = logging.getLogger(__name__)


def run_whisper_container():
    """
    Launch whisper.cpp Docker container and return the transcribed text
    """
    logger.info("Starting Whisper container")

    cmd = [
        "docker", "run", "--rm",
        "--name", WHISPER_CONTAINER_NAME,  # Container name for easy stop
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
    logger.info("Whisper container finished")

    return output


def stop_container_after_delay(delay_seconds: int):
    """
    Wait for a given delay and stop the Whisper container
    """
    logger.info(f"Stop thread started, waiting {delay_seconds} seconds")
    time.sleep(delay_seconds)

    logger.info("Stopping Whisper container")
    subprocess.run(
        ["docker", "stop", WHISPER_CONTAINER_NAME],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def run_stt_with_timeout():
    """
    Run STT with a watchdog thread that stops the container after 10 seconds
    """
    # Thread that runs the Whisper container
    whisper_thread = threading.Thread(
        target=run_whisper_container,
        name="WhisperThread"
    )

    # Thread that stops the container after 10 seconds
    stop_thread = threading.Thread(
        target=stop_container_after_delay,
        args=(10,),
        name="WhisperStopThread"
    )

    whisper_thread.start()
    stop_thread.start()

    whisper_thread.join()
    stop_thread.join()


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
