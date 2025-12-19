import subprocess
import logging
import threading
import time
from voice_recorder import start_recording
from whisperv3 import transcribe_audio, init
from flask import Flask

flaskApp = Flask(__name__)

@flaskApp.route('/start_session', methods=['GET'])
def start_session():
    name = run_stt_with_timeout()
    # return {"recognized_name": name}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

PROJECT_PATH = "/home/avatar/output"
WHISPER_CONTAINER_PATH = "/opt/whisper.cpp/output"
WHISPER_CONTAINER_NAME = "whisper_stt_container"

pipe = init()

logger = logging.getLogger(__name__)

def run_stt_with_timeout():
    record_path = start_recording()
    print("Recording saved at:", record_path)
    print("Starting transcription...")
    transcribe_audio(pipe, record_path)
    return

def main():
    flaskApp.run(host='0.0.0.0', port=5007)

if __name__ == "__main__":
    main()
