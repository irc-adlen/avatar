FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV WHISPER_MODEL=base

RUN apt-get update && apt-get install -y \
    git \
    cmake \
    build-essential \
    libsdl2-dev \
    libasound2-dev \
    libpulse-dev \
    pkg-config \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://github.com/ggml-org/whisper.cpp.git
WORKDIR /app/whisper.cpp

RUN chmod +x ./models/download-ggml-model.sh

# 🔥 Build avec CUDA
RUN cmake -B build \
    -DWHISPER_SDL2=ON \
    -DGGML_CUDA=ON \
    && cmake --build build -j --config Release

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
