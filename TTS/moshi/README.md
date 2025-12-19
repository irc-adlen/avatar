# Setup Guide

This guide details how to set up a local, offline, and low-latency text-to-speech server using Moshi/Kyutai. It is optimized for NVIDIA GPUs.

## 1. Prerequisites

* **OS**: Linux (Ubuntu 22.04+ recommended)
* **GPU**: NVIDIA RTX 3090 (or equivalent) with drivers installed (Driver 535+).
* **System Tools**:
```bash
sudo apt update
sudo apt install -y build-essential pkg-config libssl-dev libasound2-dev libportaudio2 git python3-pip python3-venv nvidia-cuda-toolkit ffmpeg
```


* **Rust**:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
```

## 2. Installation

### A. Python Environment

Create a virtual environment to keep dependencies clean.

```bash
cd ~
# Clone the repository
git clone https://github.com/kyutai-labs/delayed-streams-modeling.git
cd delayed-streams-modeling

# Create and activate venv
python3 -m venv venv_moshi
source venv_moshi/bin/activate

# Install basic dependencies
pip install --upgrade pip
pip install "moshi==0.2.11" sphn sounddevice huggingface_hub msgpack websockets pydantic
```

### B. Force CUDA Support for PyTorch

**Crucial Step:** Standard `pip install` often pulls the CPU-only version, causing slow generation (50s/sec). Force the CUDA version:

```bash
pip install --force-reinstall torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### C. Compile the Rust Server

Compile the server with CUDA support enabled.

```bash
# Ensure nvcc is found
export CUDA_HOME=/usr/lib/nvidia-cuda-toolkit
export PATH=$CUDA_HOME/bin:$PATH

# Compile
cargo install --features cuda moshi-server
```

## 3. Model & Voice Setup

We download models locally to ensure full offline capability.

### 3.1. Create directory structure
```bash
mkdir -p data_moshi/model
mkdir -p data_moshi/voices
```

### 3.2. Download the Main Model (Moshi TTS 1.6B)
```bash
hf download kyutai/tts-1.6b-en_fr --local-dir data_moshi/model
```

### 3.3. Download Voices

[Voices repo](https://huggingface.co/kyutai/tts-voices/tree/main) | [Voices showcase](https://kyutai.org/tts) 

#### Voices used in this project:

- default (US, f):
```bash
# Example manual download:
wget "https://huggingface.co/kyutai/tts-voices/resolve/main/expresso/ex01-ex02_default_001_channel1_168s.wav.1e68beda%40240.safetensors?download=true" -O data_moshi/voices/
```

## 4. Configuration (`config-local.toml`)

Create a file named `config-local.toml` at the root of the project.
**Important:** Do not include the `.1e68beda@240.safetensors` suffix in the `default_voice` field; the code adds it automatically.

```toml
static_dir = "./static/"
log_dir = "/tmp/tts-logs"
instance_name = "tts"
authorized_ids = ["public_token"]

[modules.tts_py]
hf_repo = "data_moshi/model"
type = "Py"
path = "/api/tts_streaming"
# On pointe vers le tokenizer qu'on vient de télécharger
text_tokenizer_file = "data_moshi/model/tokenizer_spm_8k_en_fr_audio.model"
batch_size = 8
text_bos_token = 1

[modules.tts_py.py]
log_folder = "/tmp/moshi-server-logs"
# On pointe vers notre dossier de voix local
voice_folder = "data_moshi/voices"
# On définit notre voix téléchargée comme défaut
default_voice = "default_voice.wav"

# Paramètres de qualité
cfg_coef = 2.0
cfg_is_no_text = true
padding_between = 1
n_q = 24
padding_bonus = -1
```

## 5. Running the Server

**The "Magic Command" for High-End Machines:**
On machines with many CPU cores (like Threadripper), `moshi-server` tries to spawn 64+ workers, crashing the NVIDIA driver (`CurandError`).

Run this in Terminal 1 (keep it open):

```bash
source venv_moshi/bin/activate

moshi-server worker --config config-local.toml
```

*Wait until you see:* `Worker ready` / `listening on http://0.0.0.0:8080`

# 6. Install Ollama and Download Model

Follow the instructions at https://ollama.com/docs/installation to install Ollama on your system.
Then, download the desired model (e.g., Qwen2.5:32B):

```bash
ollama pull qwen2.5:32b
```

## 7. Running the Streaming Client

First, edit `run_offline_agent.py` to set the model you downloaded with Ollama (e.g., `qwen2.5:32b`).

In Terminal 2, run the offline agent:

```bash
source venv_moshi/bin/activate
python TTS/tests/kyutai_v2/run_offline_agent.py
```

## 8. Testing

Type your text prompts in the Terminal running `run_offline_agent.py`. The agent will respond with synthesized speech using the local Moshi TTS server.