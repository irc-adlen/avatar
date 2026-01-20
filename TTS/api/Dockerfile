# Utilisation d'une image Python légère (Debian slim)
FROM python:3.10-slim

# Empêche Python d'écrire les fichiers .pyc et force l'affichage des logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installation des dépendances système minimales (souvent requises pour les libs réseau)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Création du dossier de travail
WORKDIR /app

# Installation des librairies Python
# FastAPI/Uvicorn : Pour l'API REST
# Websockets : Pour le streaming audio
# Aiohttp : Pour les appels asynchrones vers le Cerveau
# Msgpack : Pour décoder le format binaire de Moshi
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    websockets \
    aiohttp \
    msgpack \
    pydantic \
    requests

# Copie du code source
COPY main.py /app/main.py

# Exposition du port
EXPOSE 8001

# Lancement de l'orchestrateur
CMD ["python3", "main.py"]