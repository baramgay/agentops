FROM python:3.11-slim

WORKDIR /app

# Install core dependencies only.
# win10toast is Windows-only; chromadb/sentence-transformers are heavy optional deps
# that require a running ChromaDB instance — omit for zero-dependency startup.
RUN pip install --no-cache-dir \
    "fastapi>=0.110.0" \
    "uvicorn[standard]>=0.27.0" \
    "pydantic>=2.0.0" \
    "openai>=1.0.0" \
    "python-dotenv>=1.0.0" \
    "websockets"

# Copy application code and static assets
COPY scripts/ ./scripts/
COPY agents/ ./agents/
COPY wiki/ ./wiki/
COPY index.html metaverse.html favicon.svg ./

# Copy data files (overridden by volume mounts in production)
COPY agent_status.json issues.json projects.json ./

# AGENTS_HOME points to the working directory so scripts resolve paths correctly
ENV AGENTS_HOME=/app

EXPOSE 8000

CMD ["python", "scripts/api_server.py"]
