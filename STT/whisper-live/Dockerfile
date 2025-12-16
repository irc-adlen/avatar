FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Default model (can be overridden at runtime)
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

# Clone whisper.cpp
RUN git clone https://github.com/ggml-org/whisper.cpp.git
WORKDIR /app/whisper.cpp

# Download ALL models script (model chosen at runtime)
RUN chmod +x ./models/download-ggml-model.sh

# Build with SDL2 support
RUN cmake -B build -DWHISPER_SDL2=ON \
    && cmake --build build -j --config Release

# Entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
