FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements and install
COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and faces directory into the image
COPY ./stt.py ./stt.py

CMD ["python", "stt.py"]
