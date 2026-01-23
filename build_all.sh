#!/bin/bash

# Arrêter le script dès qu'une commande échoue
set -e

echo "🚀 Démarrage du build global..."

# Liste des images au format "CHEMIN:TAG"
declare -a images=(
    "./STT:stt"
    "./Avatar:avatar"
    "./FaceRecognition/python:faceapp"
    "./TTS/api:cpe-orchestrator"
    "./LLM:cpe-brain"
    "./TTS/moshi:moshi_server"
)

# Boucle sur chaque élément de la liste
for entry in "${images[@]}"; do
    # Séparation du chemin et du tag
    dir="${entry%%:*}"
    tag="${entry##*:}"

    echo ""
    echo "-------------------------------------------------------"
    echo "🛠️  Construction de l'image '$tag' depuis '$dir'..."
    echo "-------------------------------------------------------"
    
    # Commande de build
    docker build -t "$tag" "$dir"
done

echo ""
echo "✅ Tous les builds sont terminés avec succès !"