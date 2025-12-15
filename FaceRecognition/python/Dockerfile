FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install minimal system packages required for OpenCV and some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libsm6 \
    libxcb1 \
    libxkbcommon-x11-0 \
    libxcb-xinerama0 \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY python/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and faces directory into the image
COPY python/faceRecognition.py ./faceRecognition.py
COPY python/faces ./faces

# Ensure Qt uses xcb platform plugin by default inside container
ENV QT_QPA_PLATFORM=xcb

CMD ["python", "faceRecognition.py"]
