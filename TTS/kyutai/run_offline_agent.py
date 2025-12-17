import asyncio
import subprocess
import websockets
import sys
import msgpack
import threading
import numpy as np
import sounddevice as sd
import re

# ================= CONFIGURATION =================
OLLAMA_MODEL = "qwen2.5:32b"
SAMPLE_RATE = 24000
FRAME_SIZE = 1920

# ADAPTEZ CES CHEMINS SELON VOS FICHIERS LOCAUX
# Chemins relatifs à votre dossier 'voice_folder' défini dans config-tts.toml
VOICES = {
    "neutre": "default_voice_v2.wav", 
    "joyeux": "expresso/ex03-ex01_happy_001_channel1_334s.wav",
    "triste": "expresso/ex03-ex02_sad-sympathetic_001_channel2_400s.wav",
    "confus": "expresso/ex03-ex01_confused_001_channel1_909s.wav",
    "surpris": "expresso/ex04-ex03_whisper_002_channel2_266s.wav"
}

DEFAULT_EMOTION = "neutre"
# =================================================

async def play_audio_stream(audio_queue):
    """Joue l'audio reçu dans la file d'attente."""
    finished = False
    def callback(outdata, frames, time, status):
        nonlocal finished
        if status: print(status, file=sys.stderr)
        try:
            data = audio_queue.get_nowait()
            if data is None:
                finished = True
                outdata.fill(0)
                return
            if len(data) < len(outdata):
                outdata[:len(data), 0] = data
                outdata[len(data):, 0] = 0
            else:
                outdata[:, 0] = data[:len(outdata)]
        except asyncio.QueueEmpty:
            outdata.fill(0)

    with sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, callback=callback, blocksize=FRAME_SIZE):
        while not finished:
            await asyncio.sleep(0.1)

async def moshi_tts_client(text_queue, voice_file):
    """Reçoit du texte et l'envoie au serveur Moshi avec la voix spécifiée."""
    
    # Construction de l'URL avec la voix dynamique
    # Note : On encode l'URL correctement pour gérer les caractères spéciaux
    from urllib.parse import quote
    encoded_voice = quote(voice_file)
    uri = f"ws://localhost:8080/api/tts_streaming?auth_id=public_token&format=PcmMessagePack&voice={encoded_voice}"

    headers = {"kyutai-api-key": "public_token"}
    audio_queue = asyncio.Queue()

    try:
        async with websockets.connect(uri, additional_headers=headers) as websocket:
            print(f">>> Connecté avec la voix : {voice_file}")
            
            async def receive_audio():
                try:
                    async for message in websocket:
                        data = msgpack.unpackb(message, raw=False)
                        if data["type"] == "Audio":
                            pcm = np.array(data["pcm"], dtype=np.float32)
                            await audio_queue.put(pcm)
                            sys.stdout.write(".") 
                            sys.stdout.flush()
                except Exception:
                    pass
                finally:
                    await audio_queue.put(None)

            receiver_task = asyncio.create_task(receive_audio())
            player_task = asyncio.create_task(play_audio_stream(audio_queue))

            try:
                while True:
                    text_chunk = await text_queue.get()
                    if text_chunk is None: break
                    await websocket.send(msgpack.packb({"type": "Text", "text": text_chunk}))
                
                await websocket.send(msgpack.packb({"type": "Eos"}))
                print("\n>>> Attente fin audio...")
                await receiver_task
                await player_task
                
            except websockets.ConnectionClosed:
                print("\n>>> Connexion fermée.")
                
    except Exception as e:
        print(f"\nERREUR DE CONNEXION : Impossible de charger la voix '{voice_file}'. Vérifiez le nom du fichier.\nErreur: {e}")

def ollama_producer(prompt, text_queue, loop):
    """Génère le texte via Ollama."""
    system_instruction = "Tu es un assistant vocal français. Réponds impérativement en langue française, de manière concise et naturelle."
    full_prompt = f"{system_instruction}\nUtilisateur: {prompt}"

    process = subprocess.Popen(
        ["ollama", "run", OLLAMA_MODEL, full_prompt],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1, encoding='utf-8'
    )
    buffer = ""
    while True:
        char = process.stdout.read(1)
        if not char and process.poll() is not None: break
        if char:
            sys.stdout.write(char)
            sys.stdout.flush()
            buffer += char
            if char in [' ', '\n', '.', ',', '!', '?', ';', ':']:
                if buffer:
                    asyncio.run_coroutine_threadsafe(text_queue.put(buffer), loop)
                    buffer = ""
    if buffer: asyncio.run_coroutine_threadsafe(text_queue.put(buffer), loop)
    asyncio.run_coroutine_threadsafe(text_queue.put(None), loop)

def parse_emotion(user_input):
    """Détecte [EMOTION] au début du texte."""
    match = re.match(r"^\[(\w+)\]\s*(.*)", user_input, re.IGNORECASE)
    if match:
        emotion_key = match.group(1).lower()
        clean_text = match.group(2)
        # Vérifie si l'émotion existe dans notre dictionnaire
        if emotion_key in VOICES:
            return VOICES[emotion_key], clean_text
    return VOICES[DEFAULT_EMOTION], user_input

async def main():
    while True:
        try:
            print("\n" + "="*50)
            print(f"Émotions dispos : {', '.join(VOICES.keys())}")
            user_input = input("Vous (ex: [joyeux] Bonjour) : ")
            
            if user_input.lower() in ["exit", "quit"]:
                break

            # 1. Choix de la voix
            selected_voice_file, clean_prompt = parse_emotion(user_input)
            
            text_queue = asyncio.Queue()
            loop = asyncio.get_running_loop()
            
            # 2. Lancement des threads
            threading.Thread(target=ollama_producer, args=(clean_prompt, text_queue, loop)).start()
            await moshi_tts_client(text_queue, selected_voice_file)
            
        except KeyboardInterrupt:
            print("\nAu revoir !")
            break

if __name__ == "__main__":
    asyncio.run(main())