FROM nvcr.io/nvidia/pytorch:24.02-py3

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# (Optionnel) venv — pas obligatoire sur NGC
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY ./stt.py ./stt.py
COPY ./voice_recorder.py ./voice_recorder.py
COPY ./whisperv3.py ./whisperv3.py

CMD ["python", "stt.py"]