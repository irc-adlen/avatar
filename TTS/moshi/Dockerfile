# Image NVIDIA la plus récente (Décembre 2024)
FROM nvcr.io/nvidia/pytorch:24.12-py3

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.cargo/bin:${PATH}"

# 1. Dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    libasound2-dev \
    libportaudio2 \
    libopus-dev \
    curl \
    git \
    pkg-config \
    alsa-utils \
    ffmpeg \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# 2. Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# 3. Bitsandbytes (Local)
COPY bitsandbytes-0.45.5.zip /tmp/bitsandbytes-0.45.5.zip
RUN pip install /tmp/bitsandbytes-0.45.5.zip

# 4. Libs Python (numpy<2 est CRITIQUE)
RUN pip install --no-cache-dir \
    "numpy<2" \
    "moshi==0.2.11" \
    sphn \
    sounddevice \
    huggingface_hub \
    msgpack \
    websockets \
    pydantic

# 5. Compilation Moshi
# On force l'architecture 90 (Hopper) pour passer le build
ENV CUDA_COMPUTE_CAP=90
RUN cargo install --features cuda moshi-server

# =========================================================
# 🚨 PATCH CRITIQUE POUR GPU SM_121 (BLACKWELL / GB10) 🚨
# On désactive torch.compile proprement (ligne par ligne pour éviter les erreurs de syntaxe)
# =========================================================
RUN echo "" >> /usr/local/lib/python3.12/dist-packages/torch/__init__.py && \
    echo "import logging" >> /usr/local/lib/python3.12/dist-packages/torch/__init__.py && \
    echo "logger = logging.getLogger('GB10_PATCH')" >> /usr/local/lib/python3.12/dist-packages/torch/__init__.py && \
    echo "def compile(model, *args, **kwargs):" >> /usr/local/lib/python3.12/dist-packages/torch/__init__.py && \
    echo "    logger.warning('>>> GB10 PATCH: torch.compile() was intercepted and disabled for stability.')" >> /usr/local/lib/python3.12/dist-packages/torch/__init__.py && \
    echo "    return model" >> /usr/local/lib/python3.12/dist-packages/torch/__init__.py

# 6. Config Environnement
ENV RAYON_NUM_THREADS=1
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1

# 7. Configuration Fichiers
WORKDIR /app
RUN mkdir -p /app/data_moshi/model /app/data_moshi/voices

COPY config-docker.toml /app/config.toml
COPY start.sh /app/start.sh
COPY data_moshi/voices /app/data_moshi/voices
COPY test.py /app/test.py

# Fichier dummy pour le test de démarrage
RUN echo "import torch; print('CUDA dispo:', torch.cuda.is_available())" > /app/test.py

RUN ln -s /root/.cargo/bin/moshi-server /usr/local/bin/moshi-server
RUN chmod +x /app/start.sh

ENTRYPOINT ["/app/start.sh"]