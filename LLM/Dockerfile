# Image vLLM officielle
FROM vllm/vllm-openai:latest

# Installation des dépendances
RUN pip install --no-cache-dir \
    langchain \
    langchain-community \
    langchain-huggingface \
    langchain-chroma \
    chromadb \
    pypdf \
    sentence-transformers \
    fastapi \
    uvicorn \
    pydantic \
    einops

# Copie du code
WORKDIR /app
COPY app /app

# Exposition du port
EXPOSE 8000

# --- CORRECTION CRUCIALE ICI ---
# On écrase l'ENTRYPOINT par défaut de l'image vLLM
# Cela permet d'exécuter notre script au lieu du serveur vLLM standard
ENTRYPOINT ["python3", "main.py"]