import subprocess
import logging
import threading
import time
from voice_recorder import start_recording, try_audio_device
from whisperv3 import transcribe_audio, init
from flask import Flask, Response, request
from flask_cors import CORS

flaskApp = Flask(__name__)
CORS(flaskApp)
is_next_unknown_person = False

@flaskApp.route('/start_session', methods=['GET', 'OPTIONS'])
def start_session():
    if request.method == 'OPTIONS':
        return Response(status=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        })
    
    try:
        # Lancer le STT dans un thread séparé pour ne pas bloquer la réponse
        thread = threading.Thread(target=run_stt_with_timeout)
        thread.daemon = True
        thread.start()
        
        return Response(status=200, headers={"Access-Control-Allow-Origin": "*"}) 
    except Exception as e:
        print(f"Error in start_session: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return Response(status=500, headers={"Access-Control-Allow-Origin": "*"}) 

@flaskApp.route('/unknown_person', methods=['GET', 'OPTIONS'])
def unknown_person():
    if request.method == "OPTIONS":
        return Response(status=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        })
    
    global is_next_unknown_person
    is_next_unknown_person = True

    return Response(status=200, headers={"Access-Control-Allow-Origin": "*"}) 


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
