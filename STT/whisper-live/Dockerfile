# Base image
FROM ubuntu:22.04

# Avoid interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
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

# Set working directory
WORKDIR /app

# Clone whisper.cpp
RUN git clone https://github.com/ggml-org/whisper.cpp.git

WORKDIR /app/whisper.cpp

# Download the base model
RUN sh ./models/download-ggml-model.sh base

# Build whisper.cpp with SDL2 enabled (real-time audio)
RUN cmake -B build -DWHISPER_SDL2=ON \
    && cmake --build build -j --config Release

# Default command (can be overridden)
CMD ["./build/bin/whisper-stream", "-m", "./models/ggml-base.bin", "-l", "fr", "-t", "8"]
