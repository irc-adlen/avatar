import asyncio
import base64
import json
import websockets
import msgpack
import uvicorn
import aiohttp
import re
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict

# === CONFIGURATION ===
# L'adresse de votre Service LLM/RAG (Le "Cerveau" dockerisé)
# Si vous tournez en local, c'est localhost. Si docker, c'est le nom du service.
CPE_BRAIN_HOST = os.getenv("CPE_BRAIN_HOST", "localhost")
CPE_BRAIN_API_URL = f"http://{CPE_BRAIN_HOST}:8001/chat"

# L'adresse de Moshi (TTS)
MOSHI_HOST = os.getenv("MOSHI_HOST", "localhost")
MOSHI_WS_URL = f"ws://{MOSHI_HOST}:8080/api/tts_streaming"

AUTH_TOKEN = "public_token"

app = FastAPI(title="Orchestrateur Vocal (Gateway)")

# --- GESTIONNAIRE FLUX AUDIO (Vers le Client Web/App) ---
# (Code identique à votre version originale)
class AudioStreamManager:
    def __init__(self):
        self.active_connection: WebSocket | None = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connection = websocket
        print(">>> [System] Client Audio Connecté")

    def disconnect(self):
        self.active_connection = None
        print(">>> [System] Client Audio Déconnecté")

    async def broadcast(self, data: dict):
        if self.active_connection:
            try:
                await self.active_connection.send_json(data)
            except Exception:
                self.disconnect()

stream_manager = AudioStreamManager()

# Modèle mis à jour pour correspondre à votre nouveau système
class ChatRequest(BaseModel):
    prompt: str          # Texte utilisateur OU commande [system]
    voice: Optional[str] = "default_voice.wav"
    session_id: Optional[str] = "default"
    user_name: Optional[str] = "Inconnu" # Ajout utile pour la logique de bienvenue

# --- LOGIQUE PRINCIPALE ---
async def process_conversation(request: ChatRequest):
    from urllib.parse import urlencode
    
    # 1. Configuration Moshi (TTS)
    params = {"voice": request.voice, "format": "PcmMessagePack", "auth_id": AUTH_TOKEN}
    uri = f"{MOSHI_WS_URL}?{urlencode(params)}"
    
    try:
        # On ouvre la connexion vers le TTS (Moshi)
        async with websockets.connect(uri, additional_headers={"kyutai-api-key": AUTH_TOKEN}) as moshi_ws:
            print(f">>> [Job] Input: '{request.prompt[:30]}...' | Session: {request.session_id}")
            stop_event = asyncio.Event()

            # --- TÂCHE A : Récupérer la réponse du Cerveau (LLM + RAG) ---
            async def task_brain_producer():
                async with aiohttp.ClientSession() as session:
                    # Payload formaté pour votre nouveau service vLLM
                    payload = {
                        "text": request.prompt,
                        "session_id": request.session_id,
                        "user_name": request.user_name
                    }

                    try:
                        print(f">>> [LLM] Envoi requête vers {CPE_BRAIN_API_URL}...")
                        
                        # Appel POST simple (pas de streaming HTTP ici, le cerveau est rapide)
                        async with session.post(CPE_BRAIN_API_URL, json=payload) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                
                                # Le cerveau renvoie tout le texte d'un coup dans "prompt"
                                # Il a déjà géré la mémoire et le RAG en interne.
                                full_text = data.get("prompt", "")
                                print(f">>> [LLM] Réponse reçue : {full_text[:50]}...")

                                # ASTUCE : On découpe le texte en phrases pour l'envoyer petit à petit à Moshi
                                # Cela simule le streaming et permet au TTS de commencer vite.
                                sentences = re.split(r'(?<=[.!?]) +', full_text)
                                
                                for sentence in sentences:
                                    if sentence.strip() and not stop_event.is_set():
                                        # Envoi du texte à Moshi
                                        await moshi_ws.send(msgpack.packb({"type": "Text", "text": sentence}))
                                        # Petite pause technique pour fluidifier le buffer TTS
                                        await asyncio.sleep(0.05)
                                
                                # Signal de fin pour Moshi une fois tout le texte envoyé
                                if not stop_event.is_set():
                                    await moshi_ws.send(msgpack.packb({"type": "Eos"}))
                            else:
                                error_txt = await resp.text()
                                print(f"!!! Erreur Cerveau ({resp.status}): {error_txt}")

                    except Exception as e:
                        print(f"!!! Erreur Connexion LLM: {e}")
                        await stream_manager.broadcast({"type": "error", "message": str(e)})

            # --- TÂCHE B : Recevoir l'Audio de Moshi et l'envoyer au Client ---
            async def task_moshi_consumer():
                try:
                    async for message in moshi_ws:
                        data = msgpack.unpackb(message, raw=False)
                        msg_type = data.get("type")
                        
                        if msg_type == "Audio":
                            # Conversion PCM -> Base64 pour le client Web
                            import struct
                            pcm_bytes = struct.pack(f'{len(data["pcm"])}f', *data["pcm"])
                            b64 = base64.b64encode(pcm_bytes).decode("utf-8")
                            
                            # Envoi au Frontend
                            await stream_manager.broadcast({
                                "type": "audio",
                                "data": b64,
                                "sample_rate": 24000 # Standard Moshi
                            })
                        # Transmettre tout autre type de message
                        else:
                            await stream_manager.broadcast({"type": "meta", "content": data})

                            
                except websockets.ConnectionClosed:
                    pass
                except Exception as e:
                    print(f"!!! Moshi Error: {e}")
                finally:
                    stop_event.set()

            # Lancement parallèle des tâches
            t1 = asyncio.create_task(task_brain_producer())
            t2 = asyncio.create_task(task_moshi_consumer())
            
            # On attend que le consommateur (Audio) ait fini de tout recevoir
            await t2
            if not t1.done(): t1.cancel()

    except Exception as e:
        print(f"!!! Global Error: {e}")

# --- ENDPOINTS ---
@app.websocket("/stream/audio")
async def audio_stream_endpoint(websocket: WebSocket):
    await stream_manager.connect(websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: stream_manager.disconnect()

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    # On délègue le traitement en tâche de fond pour ne pas bloquer la requête HTTP
    background_tasks.add_task(
        process_conversation, 
        request 
    )
    return {"status": "processing_started"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)