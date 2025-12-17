import subprocess
import paho.mqtt.client as mqtt

MQTT_BROKER = "mosquitto"
MQTT_TOPIC = "stt/start"


def extract_text(lines):
    """
    Keep only real transcription lines
    """
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("["):
            continue
        if "whisper" in line.lower():
            continue
        result.append(line)
    return " ".join(result)


def run_stt():
    """
    Launch whisper.cpp Docker container and return the transcribed text
    """
    cmd = [
        "docker", "run", "--rm", "-it",
        "--gpus", "all",
        "--device", "/dev/snd",
        "whisper-gpu",
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )



    return extract_text(process.stdout)


def on_message(client, userdata, msg):
    print("MQTT trigger received")

    text = run_stt()

    print("STT result:", text)

    # Here you can:
    # - publish the result to another MQTT topic
    # - feed an LLM
    # - trigger a TTS
    # - etc.


def main():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_BROKER)
    client.subscribe(MQTT_TOPIC)

    print("Waiting for MQTT trigger...")
    client.loop_forever()


if __name__ == "__main__":
    main()
