import os
import uvicorn
import json
import re
import time
import logging
from typing import List, Optional, Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient

# --- IMPORTS IA ---
from vllm import LLM, SamplingParams
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# --- CONFIGURATION ---
MODEL_ID = "casperhansen/mistral-nemo-instruct-2407-awq"
DATA_PATH = "/data"         # Dossier monté dans Docker contenant les PDF
DB_PATH = "/vector_db"      # Dossier monté pour la persistance ChromaDB
# URI Mongo : "mongo_db" est le nom du service dans docker-compose
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo_db:27017")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CPE_BRAIN")

app = FastAPI(title="CPE Vocal Brain (Logic & Intelligence)")

# ==============================================================================
# MODULE 1: MÉMOIRE (MongoDB)
# ==============================================================================
logger.info("💾 [1/3] Connexion MongoDB...")
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    db = mongo_client["cpe_assistant_db"]
    chat_collection = db["chat_history"]
    logger.info("   ✅ Mémoire connectée.")
except Exception as e:
    logger.error(f"   ❌ Erreur Mongo: {e} (Mode sans mémoire)")
    chat_collection = None

def save_log(session_id, role, content):
    if chat_collection is not None:
        chat_collection.insert_one({
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": time.time()
        })

def get_history(session_id, limit=3):
    if chat_collection is None: return ""
    msgs = list(chat_collection.find({"session_id": session_id}).sort("timestamp", -1).limit(limit))
    msgs.reverse()
    hist = ""
    for m in msgs:
        # On ne met pas les commandes systèmes [system] dans le prompt LLM
        if not m['content'].startswith("[system]"):
            hist += f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n"
    return hist

# ==============================================================================
# MODULE 2: INTELLIGENCE (vLLM)
# ==============================================================================
logger.info("🧠 [2/3] Chargement vLLM...")

# Configuration : Puisque le TTS est ailleurs, on donne 50% du GPU au LLM
llm_engine = LLM(
    model=MODEL_ID,
    tensor_parallel_size=1,      # Utilise vos 2 GPU
    dtype="bfloat16",            # Format rapide
    max_model_len=8192,          # Contexte large
    gpu_memory_utilization=0.50, # On utilise quasi toute la VRAM dispo
    enforce_eager=True           # Optimisation démarrage
)

# Paramètres de génération
chat_sampling = SamplingParams(temperature=0.1, top_p=0.95, max_tokens=256, stop=["<|im_end|>"])
json_sampling = SamplingParams(temperature=0.1, max_tokens=128, stop=["<|im_end|>"])

logger.info("   ✅ vLLM Prêt.")

# ==============================================================================
# MODULE 3: SAVOIR (RAG)
# ==============================================================================
logger.info("📚 [3/3] Chargement RAG...")
embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")

# Initialisation de la base vectorielle
if not os.path.exists(os.path.join(DB_PATH, "chroma.sqlite3")):
    if os.path.exists(DATA_PATH) and os.listdir(DATA_PATH):
        logger.info("⚡ Indexation des PDF en cours...")
        loader = PyPDFDirectoryLoader(DATA_PATH)
        docs = loader.load()
        if docs:
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = splitter.split_documents(docs)
            vector_db = Chroma.from_documents(splits, embeddings, persist_directory=DB_PATH)
            logger.info(f"   ✅ Index créé ({len(splits)} segments).")
        else:
            vector_db = Chroma(embedding_function=embeddings, persist_directory=DB_PATH)
    else:
        logger.warning("⚠️  Aucun PDF trouvé dans /data")
        vector_db = Chroma(embedding_function=embeddings, persist_directory=DB_PATH)
else:
    logger.info("   ✅ Index existant chargé.")
    vector_db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)

# ==============================================================================
# API & LOGIQUE MÉTIER
# ==============================================================================

class BrainRequest(BaseModel):
    text: str          # Input utilisateur ou commande "[system]..."
    session_id: str
    user_name: Optional[str] = "Inconnu"

class BrainResponse(BaseModel):
    prompt: str        # Le texte que l'orchestrateur enverra au TTS
    voice: str         # Le nom du fichier voix
    session_id: str
    extra_data: Optional[Dict] = None # Données extraites (JSON)

@app.post("/chat", response_model=BrainResponse)
async def brain_endpoint(req: BrainRequest):
    
    response_text = ""
    voice_file = "default_voice.wav"
    extracted_data = None
    
    # --- A. LOGIQUE SYSTÈME (Commandes FaceID) ---
    if req.text.startswith("[system]"):
        
        # Cas A1: Utilisateur Connu
        if "Dis bonjour à" in req.text:
            match = re.search(r"Dis bonjour à (.+)", req.text)
            name = match.group(1) if match else req.user_name
            response_text = f"Bonjour {name}, ravi de vous revoir à C P E Lyon. Que puis-je faire pour vous ?"
            # On loggue la réponse pour que le LLM sache qu'on a dit bonjour
            save_log(req.session_id, "assistant", response_text)
        
        # Cas A2: Utilisateur Inconnu
        elif "Demande le prenom" in req.text:
            response_text = "Bonjour, je ne vous reconnais pas. Quel est votre prénom ?"
            save_log(req.session_id, "assistant", response_text) # Trigger important
            
    # --- B. LOGIQUE CONVERSATION ---
    else:
        save_log(req.session_id, "user", req.text)
        
        # B1. Vérification du contexte (Est-ce une réponse à "Quel est ton nom ?")
        last_bot = None
        if chat_collection is not None:
            last_bot = chat_collection.find_one(
                {"session_id": req.session_id, "role": "assistant"}, 
                sort=[("timestamp", -1)]
            )
        
        # Si la dernière phrase du robot contenait "prénom"...
        if last_bot and "Quel est votre prénom" in last_bot.get('content', ''):
            logger.info("🕵️  Extraction de nom en cours...")
            
            # Prompt spécifique pour extraire du JSON
            prompt_json = f"""<s>[INST] Extrais les infos en JSON (name, filiere, age) de la phrase. 
Phrase: "{req.text}"
JSON: [/INST]"""
            out = llm_engine.generate([prompt_json], json_sampling)
            generated = out[0].outputs[0].text.strip()
            
            try:
                # Nettoyage pour isoler le JSON
                start, end = generated.find('{'), generated.rfind('}') + 1
                if start != -1:
                    extracted_data = json.loads(generated[start:end])
            except: pass

            if extracted_data and "name" in extracted_data:
                response_text = f"Enchanté {extracted_data['name']}. J'ai bien noté vos informations."
                # On pourrait changer la voix ici si on voulait
            else:
                response_text = "Je n'ai pas bien compris le prénom. Pouvez-vous répéter ?"

        # B2. Conversation RAG Classique (Si ce n'était pas une extraction de nom)
        if not response_text:
            # 1. Recherche Documentaire
            docs = vector_db.as_retriever(search_kwargs={"k": 5}).invoke(req.text)
            context = "\n".join([d.page_content for d in docs])
            
            # 2. Récupération Historique
            history = get_history(req.session_id)
            
            # 3. Prompt RAG pour Mistral
            prompt_chat = f"""<|im_start|>system
Tu es l'assistant officiel de CPE Lyon.
Ton rôle est de répondre aux questions des étudiants en utilisant UNIQUEMENT les informations du contexte ci-dessous.

RÈGLES ABSOLUES :
1. Si la réponse n'est pas dans le contexte, tu DOIS dire : "Je n'ai pas cette information dans mes documents."
2. NE JAMAIS inventer de noms, de dates ou de règlements.
3. Réponds de manière concise (2 phrases max) et orale.

CONTEXTE DE RÉFÉRENCE :
{context}<|im_end|>
{history}
<|im_start|>user
{req.text}<|im_end|>
<|im_start|>assistant
"""
            out = llm_engine.generate([prompt_chat], chat_sampling)
            response_text = out[0].outputs[0].text.strip()

        # Sauvegarde de la réponse générée
        save_log(req.session_id, "assistant", response_text)

    # --- RETOUR À L'ORCHESTRATEUR ---
    return {
        "prompt": response_text,
        "voice": voice_file,
        "session_id": req.session_id,
        "extra_data": extracted_data
    }

if __name__ == "__main__":
    # Ce service écoute sur le port 8000
    print("Démarrage du CPE Brain sur le port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)