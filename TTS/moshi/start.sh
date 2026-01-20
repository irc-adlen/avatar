#!/bin/bash
set -e

echo ">>> Démarrage du conteneur Moshi..."

# 0. Test de l'environnement CUDA
echo ">>> Test de l'environnement CUDA avec PyTorch..."
python3 /app/test.py

# 1. Téléchargement du Modèle si absent
if [ ! -f "/app/data_moshi/model/config.json" ]; then
    echo ">>> Modèle non trouvé. Téléchargement de kyutai/tts-1.6b-en_fr..."
    huggingface-cli download kyutai/tts-1.6b-en_fr --local-dir /app/data_moshi/model
else
    echo ">>> Modèle principal détecté."
fi

# 2. Téléchargement de la Voix si absente
if [ ! -f "/app/data_moshi/voices/default_voice.wav" ]; then
    echo ">>> Voix par défaut non trouvée. Téléchargement..."
    wget "https://huggingface.co/kyutai/tts-voices/resolve/main/expresso/ex01-ex02_default_001_channel1_168s.wav.1e68beda%40240.safetensors?download=true" -O /app/data_moshi/voices/default_voice.wav
else
    echo ">>> Voix par défaut détectée."
fi
# 3. Lancement du serveur
echo ">>> Lancement de moshi-server..."
exec moshi-server worker --config /app/config.toml