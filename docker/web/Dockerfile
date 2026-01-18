FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
	postgresql-client \
	netcat-traditional \
	&& rm -rf /var/lib/apt/lists/*

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

COPY web/ /app/

RUN mkdir -p /docker-init/data

COPY docker/webeval_schema.sql /docker-init/schema.sql
COPY docker/webeval_sample_data.sql /docker-init/sample_data.sql

RUN mkdir -p /docker-init/data

COPY docker/web/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
