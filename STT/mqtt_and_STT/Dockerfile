FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install docker CLI and audio dependencies for microphone access
RUN apt-get update && \
    apt-get install -y docker.io portaudio19-dev ffmpeg alsa-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ./stt.py ./stt.py
COPY ./voice_recorder.py ./voice_recorder.py
COPY ./whisperv3.py ./whisperv3.py

CMD ["python", "stt.py"]
