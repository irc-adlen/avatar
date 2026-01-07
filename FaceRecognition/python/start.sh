#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting readWebSocket.py..."
python3 readWebSocket.py &

echo "Starting faceRecognition.py..."
python3 faceRecognition.py &

# Wait for all background processes to finish
wait
