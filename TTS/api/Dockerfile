FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api_agent.py .

# On lance l'API
CMD ["uvicorn", "api_agent:app", "--host", "0.0.0.0", "--port", "8000"]