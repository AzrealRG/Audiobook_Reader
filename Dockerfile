FROM python:3.11-slim

# ffmpeg is a system dependency (used by scripts/pipeline/tts.py to concat mp3s),
# not something pip can install
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY scripts/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command; overridden by docker-compose for the worker service
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
