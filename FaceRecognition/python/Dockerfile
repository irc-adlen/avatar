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
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application and faces directory into the image
COPY faceRecognition.py /app/faceRecognition.py

COPY faces /app/faces
COPY start.sh /app/start.sh

RUN chmod +x /app/start.sh

# Ensure Qt uses xcb platform plugin by default inside container
ENV QT_QPA_PLATFORM=xcb

CMD ["/app/start.sh"]
