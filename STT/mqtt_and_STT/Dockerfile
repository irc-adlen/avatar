FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install docker CLI
RUN apt-get update && \
    apt-get install -y docker.io && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ./stt.py ./stt.py

CMD ["python", "stt.py"]
