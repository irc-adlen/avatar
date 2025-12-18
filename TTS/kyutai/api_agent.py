import asyncio
import base64
import json
import websockets
import msgpack
import uvicorn
import aiohttp
import re
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional

# === CONFIGURATION ===
MOSHI_WS_URL = "ws://localhost:8080/api/tts_streaming"
AUTH_TOKEN = "public_token"
OLLAMA_API_URL = "http://localhost:11434/api/generate"
# Modèle à adapter selon votre installation (ex: qwen2.5:32b, dolphin-mixtral, etc.)
OLLAMA_MODEL = "qwen2.5:32b" 

# === PROMPT SYSTÈME CPE LYON ===
SYSTEM_PROMPT = """
Tu es l'assistant intelligent officiel de CPE Lyon (École Supérieure de Chimie Physique Électronique).
Ton public est composé d'étudiants ingénieurs et d'enseignants-chercheurs.

Tes directives strictes sont :
1. Langue : Réponds impérativement et uniquement en français.
2. Format : Fais des phrases courtes et fluides, optimisées pour la synthèse vocale. Évite les listes à puces complexes.
3. Ton : Sois professionnel, précis, scientifique et bienveillant.
4. Contexte : Tu maîtrises les concepts de Chimie, d'Électronique et d'Informatique.
5. Concis : Va droit au but. Pas de blabla inutile.

Si on te pose une question technique, sois rigoureux. Si c'est une question logistique sur l'école, sois serviable.
"""

app = FastAPI(title="CPE Lyon - Split Architecture API")

# --- GESTIONNAIRE DE CONNEXION AUDIO ---
class AudioStreamManager:
    def __init__(self):
        self.active_connection: WebSocket | None = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connection = websocket
        print(">>> Service Audio : Connecté")

    def disconnect(self):
        self.active_connection = None
        print(">>> Service Audio : Déconnecté")

    async def broadcast(self, data: dict):
        """Envoie des données au service audio connecté s'il existe."""
        if self.active_connection:
            try:
                await self.active_connection.send_json(data)
            except Exception as e:
                print(f"Erreur d'envoi broadcast: {e}")
                self.disconnect()
        else:
            print("Warning: Données générées mais aucun service audio n'écoute !")

stream_manager = AudioStreamManager()

# --- MODÈLES ---
class ChatRequest(BaseModel):
    prompt: str
    voice: Optional[str] = "default_voice.wav"
    system: Optional[str] = SYSTEM_PROMPT

# --- COEUR DU SYSTÈME (LOGIQUE MÉTIER) ---
async def process_conversation(prompt: str, voice: str, system_instruction: str):
    """
    Cette fonction tourne en arrière-plan.
    Elle fait : Ollama -> Moshi -> Stream Manager (WebSocket)
    """
    from urllib.parse import urlencode
    
    # 1. Connexion à Moshi
    params = {"voice": voice, "format": "PcmMessagePack", "auth_id": AUTH_TOKEN}
    uri = f"{MOSHI_WS_URL}?{urlencode(params)}"
    
    try:
        async with websockets.connect(uri, additional_headers={"kyutai-api-key": AUTH_TOKEN}) as moshi_ws:
            print(f">>> Traitement : '{prompt}'")
            
            # --- TÂCHE A : Ollama -> Moshi ---
            async def task_ollama_to_moshi():
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "model": OLLAMA_MODEL, 
                        "prompt": prompt, 
                        "system": system_instruction, 
                        "stream": True
                    }
                    
                    try:
                        async with session.post(OLLAMA_API_URL, json=payload) as resp:
                            buffer = ""
                            async for chunk in resp.content:
                                if chunk:
                                    try:
                                        data = json.loads(chunk)
                                        if data.get("done"): break
                                        token = data.get("response", "")
                                        
                                        # OPTIONNEL : Envoyer le texte brut au service audio aussi
                                        await stream_manager.broadcast({"type": "text_delta", "text": token})
                                        
                                        buffer += token
                                        # Découpage par phrases/ponctuation pour Moshi
                                        if re.search(r'[\.\,\!\?\;\:]', token):
                                            if buffer.strip():
                                                await moshi_ws.send(msgpack.packb({"type": "Text", "text": buffer}))
                                            buffer = ""
                                    except: pass
                            
                            # Fin du texte
                            if buffer.strip():
                                await moshi_ws.send(msgpack.packb({"type": "Text", "text": buffer}))
                            await moshi_ws.send(msgpack.packb({"type": "Eos"}))
                            
                    except Exception as e:
                        print(f"Erreur Ollama: {e}")
                        await stream_manager.broadcast({"type": "error", "message": str(e)})

            # --- TÂCHE B : Moshi -> Service Audio (Broadcast) ---
            async def task_moshi_to_stream():
                try:
                    async for message in moshi_ws:
                        data = msgpack.unpackb(message, raw=False)
                        
                        if data["type"] == "Audio":
                            # Encodage Base64 pour le transport JSON
                            import struct
                            pcm_bytes = struct.pack(f'{len(data["pcm"])}f', *data["pcm"])
                            b64 = base64.b64encode(pcm_bytes).decode("utf-8")
                            
                            # Envoi au service audio
                            await stream_manager.broadcast({
                                "type": "audio", 
                                "data": b64,
                                "sample_rate": 24000
                            })
                            
                        elif data["type"] in ["Timestamps", "Word", "Alignment"]:
                            # Envoi des timestamps
                            await stream_manager.broadcast({
                                "type": "timestamp", 
                                "content": data
                            })
                            
                except Exception as e:
                    print(f"Erreur Moshi Recv: {e}")

            # Lancement parallèle
            t1 = asyncio.create_task(task_ollama_to_moshi())
            t2 = asyncio.create_task(task_moshi_to_stream())
            
            # On attend que Ollama finisse d'envoyer
            await t1
            # On attend un peu que Moshi finisse de traiter
            # (Note: idéalement on attendrait un signal de fin de Moshi, 
            # mais ici on laisse tourner tant que la socket est ouverte ou on timebox)
            await asyncio.wait([t2], timeout=2.0) 
            # Dans une prod réelle, on attendrait le message de fin de Moshi pour annuler t2 proprement.

    except Exception as e:
        print(f"Erreur Globale Process: {e}")
        await stream_manager.broadcast({"type": "error", "message": "Backend Error"})


# === ENDPOINTS ===

@app.websocket("/stream/audio")
async def audio_stream_endpoint(websocket: WebSocket):
    """
    Endpoint 1 : Le tuyau de sortie.
    Le service externe se connecte ici et attend les données.
    """
    await stream_manager.connect(websocket)
    try:
        while True:
            # On garde la connexion en vie.
            # On peut aussi implémenter un ping/pong ou recevoir des commandes de contrôle (pause/stop)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        stream_manager.disconnect()

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Endpoint 2 : Le déclencheur (POST classique).
    Reçoit le prompt et lance le travail en arrière-plan.
    """
    if not stream_manager.active_connection:
        # On peut choisir de rejeter ou d'accepter quand même (mode headless)
        # return HTTPException(status_code=503, detail="Aucun service audio connecté pour recevoir le flux.")
        print("ATTENTION : Aucun service audio connecté. Le son sera perdu.")

    # On lance le traitement en tâche de fond pour libérer la requête HTTP immédiatement
    background_tasks.add_task(
        process_conversation, 
        request.prompt, 
        request.voice, 
        request.system
    )
    
    return {"status": "processing_started", "message": "La génération a commencé et sera diffusée sur /stream/audio"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)