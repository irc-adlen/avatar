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
import pymongo

# === CONFIGURATION DOCKER / LOCAL ===
# Si on est dans Docker, ces variables seront définies dans le docker-compose
MOSHI_HOST = os.getenv("MOSHI_HOST", "localhost")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")

# URLs
MOSHI_WS_URL = f"ws://{MOSHI_HOST}:8080/api/tts_streaming"
# NOTE IMPORTANTE : On utilise /api/chat pour la mémoire
OLLAMA_API_URL = f"http://{OLLAMA_HOST}:11434/api/chat"

AUTH_TOKEN = "public_token"
OLLAMA_MODEL = "qwen2.5:32b" 
SYSTEM_PROMPT = (
    "Tu es l'assistant officiel. "
    "Réponds de manière concise, précise et naturelle."
)

app = FastAPI(title="Voice Assistant API with Memory")

class ConversationManager:
    def __init__(self):
        # Connexion à MongoDB
        print(f">>> Connexion à MongoDB sur {MONGO_HOST}...")
        self.client = pymongo.MongoClient(f"mongodb://{MONGO_HOST}:27017/")
        self.db = self.client["cpe_assistant_db"]
        self.collection = self.db["conversations"]
        self.max_history = 10

    def get_history(self, session_id: str, system_instruction: str):
        # On cherche la conversation dans la base
        doc = self.collection.find_one({"session_id": session_id})
        
        if not doc:
            # Si elle n'existe pas, on la crée avec le System Prompt
            initial_history = [{"role": "system", "content": system_instruction}]
            self.collection.insert_one({
                "session_id": session_id,
                "messages": initial_history
            })
            return initial_history
        
        return doc["messages"]

    def add_message(self, session_id: str, role: str, content: str):
        # 1. On récupère l'historique actuel
        doc = self.collection.find_one({"session_id": session_id})
        if not doc: return # Sécurité
        
        messages = doc["messages"]
        
        # 2. On ajoute le nouveau message
        messages.append({"role": role, "content": content})
        
        # 3. Gestion de la fenêtre glissante (On garde System + les 10 derniers)
        if len(messages) > self.max_history + 1:
            system_msg = messages[0]
            recent_msgs = messages[-(self.max_history):]
            messages = [system_msg] + recent_msgs
        
        # 4. Mise à jour dans MongoDB
        self.collection.update_one(
            {"session_id": session_id},
            {"$set": {"messages": messages}}
        )

# Instance globale
try:
    memory = ConversationManager()
except Exception as e:
    print(f"!!! Erreur connexion Mongo: {e}")


# --- GESTIONNAIRE FLUX AUDIO ---
class AudioStreamManager:
    def __init__(self):
        self.active_connection: WebSocket | None = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connection = websocket
        print(">>> [System] Audio Client Connected")

    def disconnect(self):
        self.active_connection = None
        print(">>> [System] Audio Client Disconnected")

    async def broadcast(self, data: dict):
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
    session_id: Optional[str] = "default" # Identifiant pour la mémoire

# --- LOGIQUE PRINCIPALE ---
async def process_conversation(prompt: str, voice: str, system_instruction: str, session_id: str):
    from urllib.parse import urlencode
    
    # Configuration Moshi
    params = {"voice": voice, "format": "PcmMessagePack", "auth_id": AUTH_TOKEN}
    uri = f"{MOSHI_WS_URL}?{urlencode(params)}"
    
    try:
        # On se connecte à Moshi
        async with websockets.connect(uri, additional_headers={"kyutai-api-key": AUTH_TOKEN}) as moshi_ws:
            print(f">>> [Job] Prompt: '{prompt[:30]}...' | Session: {session_id}")
            stop_event = asyncio.Event()

            # --- TÂCHE A : Ollama (Producteur avec Mémoire) ---
            async def task_ollama_producer():
                async with aiohttp.ClientSession() as session:
                    
                    # 1. Récupération de l'historique
                    messages = memory.get_history(session_id, system_instruction)
                    # 2. Ajout du message utilisateur
                    memory.add_message(session_id, "user", prompt)
                    
                    # 3. Payload pour /api/chat
                    payload = {
                        "model": OLLAMA_MODEL,
                        "messages": messages, # On envoie tout l'historique
                        "stream": True
                    }

                    full_response = "" # Pour sauvegarder la réponse complète à la fin

                    try:
                        async with session.post(OLLAMA_API_URL, json=payload) as resp:
                            buffer = ""
                            async for chunk in resp.content:
                                if stop_event.is_set(): return
                                if chunk:
                                    try:
                                        data = json.loads(chunk)
                                        if data.get("done"): break
                                        
                                        # IMPORTANT : Parsing adapté pour /api/chat
                                        # La structure est data['message']['content']
                                        token = data.get("message", {}).get("content", "")
                                        
                                        full_response += token
                                        buffer += token
                                        
                                        # Envoi à Moshi par phrases
                                        if re.search(r'[\.\,\!\?\;\:]', token):
                                            if buffer.strip():
                                                await moshi_ws.send(msgpack.packb({"type": "Text", "text": buffer}))
                                            buffer = ""
                                    except: pass
                            
                            # Fin de génération : On sauvegarde la réponse de l'assistant
                            memory.add_message(session_id, "assistant", full_response)

                            # Envoi du reste du buffer
                            if buffer.strip() and not stop_event.is_set():
                                await moshi_ws.send(msgpack.packb({"type": "Text", "text": buffer}))
                            
                            if not stop_event.is_set():
                                await moshi_ws.send(msgpack.packb({"type": "Eos"}))
                                
                    except Exception as e:
                        print(f"!!! Ollama Error: {e}")
                        await stream_manager.broadcast({"type": "error", "message": str(e)})

            # --- TÂCHE B : Moshi (Consommateur) ---
            async def task_moshi_consumer():
                try:
                    async for message in moshi_ws:
                        data = msgpack.unpackb(message, raw=False)
                        msg_type = data.get("type")
                        
                        if msg_type == "Audio":
                            import struct
                            pcm_bytes = struct.pack(f'{len(data["pcm"])}f', *data["pcm"])
                            b64 = base64.b64encode(pcm_bytes).decode("utf-8")
                            
                            await stream_manager.broadcast({
                                "type": "audio",
                                "data": b64,
                                "sample_rate": 24000
                            })
                        else:
                            await stream_manager.broadcast({"type": "meta", "content": data})
                            
                except websockets.ConnectionClosed:
                    pass
                except Exception as e:
                    print(f"!!! Moshi Error: {e}")
                finally:
                    stop_event.set()

            # Lancement parallèle
            t1 = asyncio.create_task(task_ollama_producer())
            t2 = asyncio.create_task(task_moshi_consumer())
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
    background_tasks.add_task(
        process_conversation, 
        request.prompt, 
        request.voice, 
        request.system, 
        request.session_id # On passe l'ID de session
    )
    return {"status": "processing_started"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)