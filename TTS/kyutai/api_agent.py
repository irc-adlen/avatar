import asyncio
import base64
import json
import websockets
import msgpack
import uvicorn
import aiohttp
import re
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

# === CONFIGURATION ===
# Services Locaux
MOSHI_WS_URL = "ws://localhost:8080/api/tts_streaming"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Paramètres par défaut
AUTH_TOKEN = "public_token"
OLLAMA_MODEL = "qwen2.5:32b" 
SYSTEM_PROMPT = (
    "Tu es l'assistant officiel de CPE Lyon. "
    "Ton public est composé d'ingénieurs. "
    "Réponds en français, de manière précise, concise et scientifique."
)

app = FastAPI(title="CPE Lyon Voice Assistant API", version="1.0.0")

# --- GESTION DES FLUX (BROADCASTER) ---
class AudioStreamManager:
    """Gère la connexion WebSocket unique vers le service de diffusion (Avatar/Frontend)."""
    def __init__(self):
        self.active_connection: WebSocket | None = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connection = websocket
        print(">>> [System] Audio Stream Client Connected")

    def disconnect(self):
        self.active_connection = None
        print(">>> [System] Audio Stream Client Disconnected")

    async def broadcast(self, data: dict):
        """Envoie les données au client connecté."""
        if self.active_connection:
            try:
                await self.active_connection.send_json(data)
            except Exception:
                self.disconnect()

stream_manager = AudioStreamManager()

class ChatRequest(BaseModel):
    prompt: str
    voice: Optional[str] = "default_voice.wav"
    system: Optional[str] = SYSTEM_PROMPT

# --- COEUR DU SYSTÈME ---
async def process_conversation(prompt: str, voice: str, system_instruction: str):
    from urllib.parse import urlencode
    
    # Configuration de la connexion Moshi
    params = {"voice": voice, "format": "PcmMessagePack", "auth_id": AUTH_TOKEN}
    uri = f"{MOSHI_WS_URL}?{urlencode(params)}"
    
    try:
        async with websockets.connect(uri, additional_headers={"kyutai-api-key": AUTH_TOKEN}) as moshi_ws:
            print(f">>> [Job] Processing prompt: '{prompt[:30]}...'")
            stop_event = asyncio.Event()

            # --- Tâche A : Ollama (Génération Texte) ---
            async def task_ollama_producer():
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "model": OLLAMA_MODEL, "prompt": prompt, 
                        "system": system_instruction, "stream": True
                    }
                    try:
                        async with session.post(OLLAMA_API_URL, json=payload) as resp:
                            buffer = ""
                            async for chunk in resp.content:
                                if stop_event.is_set(): return
                                if chunk:
                                    try:
                                        data = json.loads(chunk)
                                        if data.get("done"): break
                                        
                                        token = data.get("response", "")
                                        buffer += token
                                        
                                        # Envoi à Moshi par phrases/groupes de mots
                                        if re.search(r'[\.\,\!\?\;\:]', token):
                                            if buffer.strip():
                                                await moshi_ws.send(msgpack.packb({"type": "Text", "text": buffer}))
                                            buffer = ""
                                    except: pass
                            
                            # Envoi du reste du buffer et signal de fin
                            if buffer.strip() and not stop_event.is_set():
                                await moshi_ws.send(msgpack.packb({"type": "Text", "text": buffer}))
                            
                            if not stop_event.is_set():
                                await moshi_ws.send(msgpack.packb({"type": "Eos"}))
                                
                    except Exception as e:
                        print(f"!!! Ollama Error: {e}")
                        await stream_manager.broadcast({"type": "error", "message": str(e)})

            # --- Tâche B : Moshi (Synthèse Audio) ---
            async def task_moshi_consumer():
                try:
                    async for message in moshi_ws:
                        data = msgpack.unpackb(message, raw=False)
                        msg_type = data.get("type")
                        
                        if msg_type == "Audio":
                            # Encodage PCM Audio
                            import struct
                            pcm_bytes = struct.pack(f'{len(data["pcm"])}f', *data["pcm"])
                            b64 = base64.b64encode(pcm_bytes).decode("utf-8")
                            
                            await stream_manager.broadcast({
                                "type": "audio",
                                "data": b64,
                                "sample_rate": 24000
                            })
                            
                        else:
                            # Envoi des métadonnées (Timestamps, Alignement)
                            # C'est ici que 'Alignment' ou 'TextToken' passent
                            await stream_manager.broadcast({
                                "type": "meta",
                                "content": data
                            })
                            '
                except websockets.ConnectionClosed:
                    pass # Fin normale du flux
                except Exception as e:
                    print(f"!!! Moshi Error: {e}")
                finally:
                    await stream_manager.broadcast({
                        "type": "meta",
                        "content": {"type": "Eos"}
                    })
                    stop_event.set() # Arrêt forcé du producer

            # Exécution parallèle
            t_producer = asyncio.create_task(task_ollama_producer())
            t_consumer = asyncio.create_task(task_moshi_consumer())
            
            await t_consumer
            if not t_producer.done(): t_producer.cancel()

    except Exception as e:
        print(f"!!! Global Error: {e}")

# --- ENDPOINTS ---

@app.websocket("/stream/audio")
async def audio_stream_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Audio/Metadata output."""
    await stream_manager.connect(websocket)
    try:
        while True: await websocket.receive_text() # Keep-alive loop
    except WebSocketDisconnect:
        stream_manager.disconnect()

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    """HTTP POST endpoint to trigger generation."""
    if not stream_manager.active_connection:
        print(">>> [Warning] No audio client connected. Audio will be lost.")
    
    background_tasks.add_task(process_conversation, request.prompt, request.voice, request.system)
    return {"status": "processing_started"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)