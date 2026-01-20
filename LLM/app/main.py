import os
import uvicorn
import base64
import json
import re
import time
import torch
import io
import logging
from typing import List, Optional, Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from scipy.io.wavfile import write as write_wav

# --- MODULE IMPORTS ---
# ROLE: The Brain (Inference Engine)
from vllm import LLM, SamplingParams
# ROLE: The Mouth (Text-to-Speech)
from TTS.api import TTS
# ROLE: The Knowledge (RAG)
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# --- CONFIGURATION ---
MODEL_ID = "mistralai/Mistral-Nemo-Instruct-2407"
TTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
DATA_PATH = "/data"
DB_PATH = "/vector_db"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
VOICE_REF = "default_voice.wav"

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CPE_MONOLITH")

app = FastAPI(title="CPE Vocal Assistant - Monolithic Core")

# ==============================================================================
# MODULE 1: LONG-TERM MEMORY (MongoDB)
# ROLE: Stores conversation history and context between sessions.
# ==============================================================================
logger.info("💾 [MODULE 1] Connecting to Memory (MongoDB)...")
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    db = mongo_client["cpe_assistant_db"]
    chat_collection = db["chat_history"]
    logger.info("   ✅ Memory Connected.")
except Exception as e:
    logger.error(f"   ❌ Memory Error: {e} (Running without persistent memory)")
    chat_collection = None

def save_memory(session_id, role, content):
    if chat_collection is not None:
        chat_collection.insert_one({
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": time.time()
        })

def get_memory(session_id, limit=3):
    if chat_collection is None: return ""
    msgs = list(chat_collection.find({"session_id": session_id}).sort("timestamp", -1).limit(limit))
    msgs.reverse()
    hist = ""
    for m in msgs:
        # Filter out system commands from context to avoid confusion
        if not m['content'].startswith("[system]"):
            hist += f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n"
    return hist

# ==============================================================================
# MODULE 2: THE BRAIN (vLLM)
# ROLE: Generates intelligence, answers questions, and extracts JSON data.
# ==============================================================================
logger.info("🧠 [MODULE 2] Loading Brain (vLLM)...")
# OPTIMIZATION: We restrict vLLM to 50% GPU to leave room for TTS.
llm_engine = LLM(
    model=MODEL_ID,
    tensor_parallel_size=2,       # Uses both GPUs
    dtype="bfloat16",
    max_model_len=8192,
    gpu_memory_utilization=0.5,   # CRITICAL: Only use 50% VRAM
    enforce_eager=True            # CRITICAL: Disable Graph capture to save RAM
)
# Sampling for chat (creative)
chat_sampling = SamplingParams(temperature=0.7, top_p=0.9, max_tokens=256, stop=["<|im_end|>"])
# Sampling for data extraction (strict)
json_sampling = SamplingParams(temperature=0.1, max_tokens=128, stop=["<|im_end|>"])
logger.info("   ✅ Brain Loaded.")

# ==============================================================================
# MODULE 3: THE MOUTH (Coqui TTS)
# ROLE: Converts text responses into audio bytes (WAV).
# ==============================================================================
logger.info("🔊 [MODULE 3] Loading Mouth (XTTS v2)...")
os.environ["COQUI_TOS_AGREED"] = "1"
# We force TTS onto the first GPU (shared with half of vLLM)
tts_engine = TTS(model_name=TTS_MODEL).to("cuda:0")
logger.info("   ✅ Mouth Loaded.")

def generate_speech(text):
    """Generates audio and returns Base64 string."""
    # Clean text for better pronunciation (remove markdown)
    clean_text = re.sub(r'[*_#`]', '', text)
    wav = tts_engine.tts(text=clean_text, speaker_wav=VOICE_REF, language="fr")
    
    bio = io.BytesIO()
    write_wav(bio, 24000, wav)
    return base64.b64encode(bio.getvalue()).decode("utf-8")

# ==============================================================================
# MODULE 4: KNOWLEDGE BASE (RAG / ChromaDB)
# ROLE: Indexes PDFs and retrieves relevant context.
# ==============================================================================
logger.info("📚 [MODULE 4] Loading Knowledge Base (RAG)...")
embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")

if not os.path.exists(os.path.join(DB_PATH, "chroma.sqlite3")):
    if os.path.exists(DATA_PATH):
        loader = PyPDFDirectoryLoader(DATA_PATH)
        docs = loader.load()
        if docs:
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = splitter.split_documents(docs)
            vector_db = Chroma.from_documents(splits, embeddings, persist_directory=DB_PATH)
            logger.info(f"   ✅ Index Created ({len(splits)} chunks).")
        else:
            vector_db = Chroma(embedding_function=embeddings, persist_directory=DB_PATH)
    else:
        vector_db = Chroma(embedding_function=embeddings, persist_directory=DB_PATH)
else:
    logger.info("   ✅ Existing Index Loaded.")
    vector_db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)

# ==============================================================================
# API LOGIC & ORCHESTRATION
# ==============================================================================

class UserInput(BaseModel):
    text: str          # Input text or "[system] command"
    session_id: str    # Unique session ID
    user_name: Optional[str] = "Inconnu"

class BotOutput(BaseModel):
    text: str          # Text response
    audio: str         # Base64 WAV Audio
    extra_data: Optional[Dict] = None # Extracted JSON info (if any)

@app.post("/chat", response_model=BotOutput)
async def main_pipeline(req: UserInput):
    """
    Main entry point. Orchestrates Logic -> Memory -> RAG -> LLM -> TTS.
    """
    response_text = ""
    extracted_data = None
    
    # --- LOGIC PATH A: SYSTEM COMMANDS (Face Recognition) ---
    if req.text.startswith("[system]"):
        
        # Case A1: Known User -> Welcome
        if "Dis bonjour à" in req.text:
            match = re.search(r"Dis bonjour à (.+)", req.text)
            name = match.group(1) if match else "l'ami"
            response_text = f"Bonjour {name}, ravi de vous revoir à C P E Lyon. Que puis-je faire pour vous ?"
            # We don't save system triggers in user history, only the bot response
            save_memory(req.session_id, "assistant", response_text)
        
        # Case A2: Unknown User -> Ask Name
        elif "Demande le prenom" in req.text:
            response_text = "Bonjour, je ne vous reconnais pas. Quel est votre prénom ?"
            save_memory(req.session_id, "assistant", response_text) # Critical for context tracking
            
    # --- LOGIC PATH B: USER CONVERSATION ---
    else:
        # Save user input
        save_memory(req.session_id, "user", req.text)
        
        # Check Context: Are we waiting for a name?
        last_bot_msg = None
        if chat_collection:
            last_bot_msg = chat_collection.find_one(
                {"session_id": req.session_id, "role": "assistant"}, 
                sort=[("timestamp", -1)]
            )
        
        # Case B1: User is answering the name question
        if last_bot_msg and "Quel est votre prénom" in last_bot_msg.get('content', ''):
            logger.info("🕵️ DATA EXTRACTION MODE DETECTED")
            
            # Use Brain to extract JSON
            prompt = f"""<s>[INST] Extract info as JSON (name, filiere, age). 
Text: "{req.text}"
JSON: [/INST]"""
            out = llm_engine.generate([prompt], json_sampling)
            generated = out[0].outputs[0].text.strip()
            
            try:
                # Parse JSON
                start, end = generated.find('{'), generated.rfind('}') + 1
                if start != -1:
                    extracted_data = json.loads(generated[start:end])
            except: pass

            if extracted_data and "name" in extracted_data:
                response_text = f"Enchanté {extracted_data['name']}. J'ai bien noté vos informations."
                # HERE: You can add a POST request to your external API
            else:
                response_text = "Je n'ai pas bien compris le prénom. Pouvez-vous répéter ?"

        # Case B2: Standard RAG Conversation
        if not response_text:
            # 1. Retrieve Knowledge
            docs = vector_db.as_retriever(search_kwargs={"k": 2}).invoke(req.text)
            context = "\n".join([d.page_content for d in docs])
            
            # 2. Retrieve History
            history = get_memory(req.session_id)
            
            # 3. Generate Answer
            prompt = f"""<|im_start|>system
Tu es l'assistant de CPE Lyon.
Réponds oralement, de manière concise (2 phrases max), en français.
Utilise le contexte suivant :
{context}<|im_end|>
{history}
<|im_start|>user
{req.text}<|im_end|>
<|im_start|>assistant
"""
            out = llm_engine.generate([prompt], chat_sampling)
            response_text = out[0].outputs[0].text.strip()
            
            save_memory(req.session_id, "assistant", response_text)

    # --- FINAL STEP: GENERATE AUDIO ---
    # Convert the final text to audio
    audio_b64 = generate_speech(response_text)
    
    return {
        "text": response_text,
        "audio": audio_b64,
        "extra_data": extracted_data
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)