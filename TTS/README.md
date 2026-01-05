# 📘 CPE Lyon Voice Assistant – Technical Deployment Guide - DOCKER

## 1. System Overview

This project implements a **Split Architecture** for a low-latency, offline voice assistant. It runs entirely within Docker containers orchestrated via Docker Compose.

### The Stack

* **`moshi_server` (GPU)**: Kyutai Neural TTS engine. Stream audio via WebSocket.
* **`moshi_ollama` (GPU)**: Qwen 2.5 LLM. Handles intelligence and reasoning.
* **`moshi_mongo` (CPU)**: MongoDB Database. Persists conversation history (Memory).
* **`moshi_agent` (CPU)**: Python FastAPI Controller. Orchestrates the flow between User, Memory, LLM, and TTS.

---

## 2. Prerequisites

**Hardware:**

* **GPU:** NVIDIA RTX 3090 (or equivalent) with 24GB+ VRAM.
* **OS:** Linux (Ubuntu 22.04+ recommended).

**Software:**

* **Docker Engine** & **Docker Compose**.
* **NVIDIA Container Toolkit**: Mandatory for GPU passthrough.
* *Verification:* `docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi`



---

## 3. Directory Structure

Ensure your project directory matches this structure **exactly** to avoid volume mapping errors.

```text
cpe-assistant/
├── docker-compose.yml
├── client_test.py           # Local audio listener script
├── agent/
│   ├── Dockerfile
│   ├── requirements.txt     # Must include: pymongo, websockets, fastapi, uvicorn...
│   └── api_agent.py         # The main Python orchestrator
└── moshi/
    ├── Dockerfile
    ├── config.toml          # Paths must be absolute: /app/data_moshi/...
    ├── start.sh             # Entrypoint
    └── data_moshi/          # Mounted Volume
        └── voices/
            └── default_voice.wav  <-- already present in the image

```

---

## 4. Critical Configuration Checks

Before running, check this file to prevent common crashes.

### A. `agent/api_agent.py` (Memory Backend)

Ensure the script is configured to use the Docker network names.

```python
MOSHI_HOST = os.getenv("MOSHI_HOST", "localhost")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")

```

---

## 5. Deployment

### Step 1: Build and Run

Run this command from the root directory. It will compile Rust (Moshi), install Python deps, and download Docker images.

```bash
sudo docker compose up --build -d

```

*Note: The first run will take time as it downloads the ~10GB Moshi model and the Ollama model.*

### Step 2: Health Check

Verify that all 4 containers are running and healthy.

```bash
sudo docker compose logs -f

```

**Success Indicators:**

* `moshi_server`: `Listening on http://0.0.0.0:8080`
* `moshi_ollama`: `Listening on [::]:11434`
* `moshi_mongo`: `Waiting for connections on port 27017`
* `moshi_agent`: `Uvicorn running on http://0.0.0.0:8000`

---

## 6. Testing the System

Since the architecture is decoupled, testing requires two terminals: one to **hear** (Client) and one to **speak** (Trigger).

### Terminal 1: The Audio Receiver

Run the [test_listener.py](moshi/test_listener.py) on your host machine to connect to the WebSocket.

```bash
# Install dependencies if needed
pip install websockets sounddevice numpy colorama

# Run client
python moshi/test_listener.py

```

*Output: `✅ Connected! Waiting for audio...*`

### Terminal 2: The Chat Trigger

Send a JSON payload to the API.

**Test 1: General Conversation**

```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
           "prompt": "Hello, introduce yourself briefly.",
           "session_id": "user_demo"
         }'

```

*Result: You should hear audio in Terminal 1.*

**Test 2: Memory Persistence (MongoDB)**

1. **Feed info:** `curl ... -d '{"prompt": "My name is Alex.", "session_id": "user_alex"}'`
2. **Restart Stack:** `sudo docker compose restart agent`
3. **Ask info:** `curl ... -d '{"prompt": "What is my name?", "session_id": "user_alex"}'`
*Result: The AI should reply "Your name is Alex."*

---

## 7. Troubleshooting

| Symptom | Probable Cause | Solution |
| --- | --- | --- |
| **Connection Refused (Port 8080)** | Moshi crashed or is booting. | Check logs (`docker logs moshi_server`). Ensure `--workers 1` is set. |
| **Audio plays too fast/static** | Sample rate mismatch. | Ensure `client_test.py` expects **24000Hz** Raw PCM Float32. |
| **Memory not working** | MongoDB connection failed. | Check `docker logs moshi_agent`. Ensure `pymongo` is in `requirements.txt`. |
| **Ollama "Model not found"** | Model wasn't pulled. | Run `sudo docker exec -it moshi_ollama ollama pull qwen2.5:32b`. |

---

## 8. Management Commands

* **Stop everything:** `sudo docker compose down`
* **Rebuild only the Python Agent:** `sudo docker compose up --build -d agent`
* **View live logs:** `sudo docker compose logs -f --tail=100`