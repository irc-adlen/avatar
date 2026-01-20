FROM vllm/vllm-openai:latest

# INSTALLATION OF ALL MODULES (Brain, Mouth, Memory, RAG)
RUN pip install --no-cache-dir \
    fastapi uvicorn pydantic requests \
    pymongo \
    TTS \
    langchain langchain-community langchain-huggingface langchain-chroma chromadb pypdf sentence-transformers \
    scipy

WORKDIR /app
COPY main.py /app/main.py
# Copy your voice reference file for cloning
COPY default_voice.wav /app/default_voice.wav 

# Create data directories
RUN mkdir -p /data /vector_db

# Run the Monolith
ENTRYPOINT ["python3", "main.py"]