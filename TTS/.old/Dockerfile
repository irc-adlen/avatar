FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
RUN pip install --no-cache-dir setuptools typeguard pyyaml "piper-tts[http]"

# Copy TTS sources (build context should be the TTS/ directory)
COPY . /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV VOICE=fr_FR-tom-medium
ENV DATA_DIR=/app/voices
ENV PORT=5002

ENTRYPOINT ["/entrypoint.sh"]
