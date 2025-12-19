#!/bin/sh
set -eu

# Usage: entrypoint for Piper TTS inside container
VOICE=${VOICE:-fr_FR-tom-medium}
DATA_DIR=${DATA_DIR:-/app/voices}
PORT=${PORT:-5000}

mkdir -p "$DATA_DIR"

if [ "${SKIP_VOICE_DOWNLOAD:-0}" != "1" ]; then
  if [ ! -d "$DATA_DIR/$VOICE" ]; then
    echo "Downloading voice $VOICE into $DATA_DIR..."
    python3 -m piper.download_voices "$VOICE" --data-dir "$DATA_DIR"
  else
    echo "Voice $VOICE already present in $DATA_DIR"
  fi
else
  echo "SKIP_VOICE_DOWNLOAD=1 -> skipping voice download"
fi

echo "Starting Piper HTTP server: voice=$VOICE data_dir=$DATA_DIR port=$PORT"
exec python3 -m piper.http_server -m "$VOICE" --data-dir "$DATA_DIR" --port "$PORT" --host 0.0.0.0
