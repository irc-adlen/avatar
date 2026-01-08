import subprocess
import logging
import threading
import time
from voice_recorder import start_recording
from whisperv3 import transcribe_audio, init
from flask import Flask, Response

flaskApp = Flask(__name__)
is_next_unknown_person = False

@flaskApp.route('/start_session', methods=['GET'])
def start_session():
    run_stt_with_timeout()
    return Response(
            status=200,
        ) 

@flaskApp.route('/unknown_person', methods=['GET'])
def unknown_person():
    global is_next_unknown_person
    is_next_unknown_person = True
    return Response(
            status=200,
        ) 


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
    global is_next_unknown_person
    record_path = start_recording()
    print("Recording saved at:", record_path)
    print("Starting transcription...")
    transcribe_audio(pipe, record_path, is_next_unknown_person)
    is_next_unknown_person = False
    return

def main():
    flaskApp.run(host='0.0.0.0', port=5007)

if __name__ == "__main__":
    main()
