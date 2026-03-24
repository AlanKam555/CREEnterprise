FROM python:3.11-slim

WORKDIR /app

# ── Install system dependencies ──
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ──
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# ── App code ──
COPY . .

# ── Non-root user for security ──
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# ── Health check ──
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

EXPOSE 8000

# Gunicorn: 4 workers (2*CPU+1), bind to 0.0.0.0:8000, with access logs
CMD ["gunicorn", "main:app", \
     "-w", "4", \
     "-b", "0.0.0.0:8000", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "--timeout", "120"]
