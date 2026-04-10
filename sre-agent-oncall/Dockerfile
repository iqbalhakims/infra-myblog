FROM python:3.11-slim

WORKDIR /app

# Install system deps for sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/
COPY runbooks/ runbooks/

RUN pip install --no-cache-dir -e .

# Pre-ingest runbooks into Chroma at build time
RUN python -m sre_agent.rag.ingest

EXPOSE 8080

CMD ["python", "-m", "sre_agent.main"]
