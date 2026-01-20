FROM python:3.10-slim

# Libs pour l'audio
RUN apt-get update && apt-get install -y \
    libasound2 \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# On copie le script de l'agent
COPY api_agent.py .

# Port
EXPOSE 8080

CMD ["python", "api_agent.py"]