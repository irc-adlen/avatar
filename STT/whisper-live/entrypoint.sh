#!/bin/bash
set -e

MODEL_NAME="${WHISPER_MODEL}"
MODEL_PATH="./models/ggml-${MODEL_NAME}.bin"

# Download model only if missing
if [ ! -f "$MODEL_PATH" ]; then
    echo "Downloading model: ${MODEL_NAME}"
    sh ./models/download-ggml-model.sh "${MODEL_NAME}"
fi

echo "Starting whisper with model: ${MODEL_NAME}"

exec ./build/bin/whisper-stream \
    -m "$MODEL_PATH" \
    -l fr \
    -t 8
