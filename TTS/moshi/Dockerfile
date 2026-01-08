# On part d'une image PyTorch avec CUDA pour avoir les drivers GPU
FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# 1. Installation des dépendances système (Audio + Rust reqs)
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libssl-dev \
    libasound2-dev \
    libportaudio2 \
    curl \
    git \
    wget \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 2. Installation de Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# 3. Installation des dépendances Python
# On installe moshi et huggingface_hub
RUN pip install --upgrade pip
RUN pip install "torch==2.9.0+cu128" --extra-index-url https://download.pytorch.org/whl/cu128
RUN pip install "moshi==0.2.11" sphn sounddevice huggingface_hub msgpack websockets pydantic

# On définit l'architecture GPU manuellement (86 = RTX 3090 / Ampere)
# Cela empêche le script de chercher nvidia-smi pendant le build
ENV CUDA_COMPUTE_CAP=86

# 4. Compilation de moshi-server avec support CUDA
# C'est l'étape longue, mais elle ne se fera qu'une fois au build
RUN cargo install --features cuda moshi-server

# On indique au système où trouver la librairie Python de Conda
ENV LD_LIBRARY_PATH="/opt/conda/lib:$LD_LIBRARY_PATH"

# 5. Préparation des dossiers
WORKDIR /app
RUN mkdir -p /app/data_moshi/model /app/data_moshi/voices

# 6. Scripts et Config
COPY config-docker.toml /app/config.toml
COPY start.sh /app/start.sh
COPY data_moshi/voices /app/data_moshi/voices
RUN chmod +x /app/start.sh

ENTRYPOINT ["/app/start.sh"]