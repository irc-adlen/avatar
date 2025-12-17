# Base image with CUDA support
FROM nvidia/cuda:12.2.0-devel-ubuntu22.04


# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive


# Install system dependencies
RUN apt-get update && apt-get install -y \
git \
cmake \
build-essential \
libsdl2-dev \
ffmpeg \
curl \
ca-certificates \
&& rm -rf /var/lib/apt/lists/*


# Set working directory
WORKDIR /opt


# Clone whisper.cpp repository
RUN git clone https://github.com/ggml-org/whisper.cpp.git


WORKDIR /opt/whisper.cpp


# Download the medium model
RUN sh ./models/download-ggml-model.sh medium


# Configure the build with CUDA and SDL2 support
RUN cmake -B build \
-DGGML_CUDA=1 \
-DWHISPER_SDL2=ON \
-DCMAKE_BUILD_TYPE=Release


# Build whisper.cpp
RUN cmake --build build -j$(nproc)


# Default command: start real-time streaming in French
CMD ["./build/bin/whisper-stream", "-m", "./models/ggml-medium.bin", "-l", "fr", "-t", "8", "-mt", "64"]