# =============================================================================
# Best Practice Dockerfile for Django Monolith — LegacyPeople
# Supports both development and production modes via environment variables:
#
#   Development container (docker compose up):
#     DEBUG=True, SECRET_KEY supplied via .env / docker-compose environment
#
#   Production container (Docker image from GHCR):
#     DEBUG=False (default), SECRET_KEY must be injected at runtime via env.
#
# NEVER embed real SECRET_KEY values into the image. Always pass at runtime.
# =============================================================================
FROM python:3.12-slim

# Python runtime best practices
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies (Node.js 20 required for Dart Sass via npx sass)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy node dependencies & install
COPY package*.json ./
RUN npm ci || npm install

# Copy Python requirements & install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy and setup entrypoint script
COPY devops/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Security best practice: Run app as a non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /entrypoint.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]
