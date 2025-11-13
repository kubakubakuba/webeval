FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    flask \
    flask-mail \
    gunicorn \
    toml \
    markdown \
    psycopg2-binary \
    python-dotenv \
    pygments

# Copy web application files from project root
COPY web/ /app/

# Copy database schema for initialization
COPY scripts/qtrvsim_web_eval.sql /docker-init/schema.sql

# Create directory for optional initial data
RUN mkdir -p /docker-init/data

# Copy entrypoint script
COPY docker/web/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
