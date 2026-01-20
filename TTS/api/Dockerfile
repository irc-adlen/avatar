# Image optimisée pour NVIDIA
FROM vllm/vllm-openai:latest

# Installation des dépendances pour la Logique, la Mémoire et le RAG
RUN pip install --no-cache-dir \
    fastapi uvicorn pydantic requests pymongo \
    langchain langchain-community langchain-huggingface langchain-chroma chromadb pypdf sentence-transformers \
    einops

# Configuration du dossier de travail
WORKDIR /app
COPY main.py /app/main.py

# Création des dossiers pour les PDF et la Base Vectorielle
RUN mkdir -p /data /vector_db

# Lancement du serveur
ENTRYPOINT ["python3", "main.py"]