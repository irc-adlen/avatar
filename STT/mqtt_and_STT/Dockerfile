FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies
RUN apt-get update && \
    apt-get install -y \
        python3 \
        python3-pip \
        ffmpeg \
        portaudio19-dev \
        alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ./stt.py ./stt.py
COPY ./voice_recorder.py ./voice_recorder.py
COPY ./whisperv3.py ./whisperv3.py

CMD ["python", "stt.py"]
