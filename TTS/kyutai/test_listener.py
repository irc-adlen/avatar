import asyncio
import websockets
import json
import base64
import numpy as np
import sounddevice as sd
import sys

# URL définie dans votre API (api_agent_split.py)
STREAM_URL = "ws://localhost:8000/stream/audio"
SAMPLE_RATE = 24000
BLOCK_SIZE = 1920  # Taille standard des paquets Moshi

async def listen_and_play():
    print(f"🔊 Connexion au flux audio : {STREAM_URL} ...")
    
    audio_queue = asyncio.Queue()
    
    # --- Lecteur Audio (Callback) ---
    def audio_callback(outdata, frames, time, status):
        if status:
            print(f"[Audio Status] {status}", file=sys.stderr)
        try:
            # On récupère le prochain paquet audio
            data = audio_queue.get_nowait()
            
            # Gestion de la taille du buffer (si le paquet est plus petit ou plus grand)
            chunk_len = len(data)
            out_len = len(outdata)
            
            if chunk_len < out_len:
                outdata[:chunk_len, 0] = data
                outdata[chunk_len:, 0] = 0
            else:
                outdata[:, 0] = data[:out_len]
                
        except asyncio.QueueEmpty:
            outdata.fill(0)

    # Démarrage de la carte son
    stream = sd.OutputStream(
        samplerate=SAMPLE_RATE, 
        channels=1, 
        callback=audio_callback,
        blocksize=BLOCK_SIZE
    )
    stream.start()

    # --- Boucle WebSocket ---
    try:
        async with websockets.connect(STREAM_URL) as ws:
            print("✅ Connecté ! En attente de données (lancez une commande curl)...")
            
            while True:
                message = await ws.recv()
                data = json.loads(message)
                msg_type = data.get("type")

                # 1. Gestion de l'Audio
                if msg_type == "audio":
                    # Décodage Base64 -> Bytes -> Numpy Float32
                    b64_data = data["data"]
                    pcm_bytes = base64.b64decode(b64_data)
                    audio_arr = np.frombuffer(pcm_bytes, dtype=np.float32)
                    
                    await audio_queue.put(audio_arr)

                # 2. Affichage des Timestamps
                elif msg_type == "timestamp":
                    content = data.get("content", {})
                    # On essaie d'extraire les champs standards, sinon on affiche tout
                    text = content.get("text") or content.get("word")
                    start = content.get("start")
                    end = content.get("end")
                    
                    if text is not None:
                        print(f"⏱️  [{start:.2f}s -> {end:.2f}s] : \"{text}\"")
                    else:
                        print(f"⏱️  Timestamp Raw: {content}")

                # 3. Affichage du texte LLM (Optionnel)
                elif msg_type == "text_delta":
                    pass # On ignore le texte brut pour se concentrer sur l'audio/timestamp
                
                elif msg_type == "meta":
                    content = data.get("content", {})
                    # Affiche le contenu brut pour débogage
                    print(f"🔍 META REÇU : {content}")
                
                elif msg_type == "error":
                    print(f"❌ ERREUR: {data['message']}")

    except websockets.ConnectionClosed:
        print("Déconnecté du serveur.")
    except Exception as e:
        print(f"Erreur inattendue : {e}")
    finally:
        stream.stop()

if __name__ == "__main__":
    try:
        asyncio.run(listen_and_play())
    except KeyboardInterrupt:
        print("\nArrêt.")