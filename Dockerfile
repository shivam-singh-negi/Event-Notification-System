FROM python:3.12-slim

# -------------------------------------------------
# Runtime safety & Python behavior
# -------------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Application port (requirement)
ENV APP_PORT=8080

WORKDIR /app

# -------------------------------------------------
# Install system dependencies (minimal)
# -------------------------------------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------
# Install Python dependencies
# -------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------
# Copy application code
# -------------------------------------------------
COPY app ./app
COPY .env .env

# -------------------------------------------------
# Expose API port
# -------------------------------------------------
EXPOSE 8080

# -------------------------------------------------
# IMPORTANT:
# - exec-form CMD (signal-safe)
# - single worker (in-memory queues!)
# -------------------------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
