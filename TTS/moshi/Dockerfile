# Utilisation d'une image avec support CUDA pour la performance
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# Installation de Moshi (et utilitaires)
RUN pip install --no-cache-dir moshi huggingface_hub

# Copie de la configuration et des voix (Intégration directe à l'image)
COPY config-local.toml /app/config.toml
COPY data_moshi/voices /data_moshi/voices

# Script de démarrage
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Port interne (ne sera pas exposé au public, juste au réseau Docker)
EXPOSE 8080

ENTRYPOINT ["/app/start.sh"]