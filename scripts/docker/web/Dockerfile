# Use Debian as the base image
FROM debian:bullseye-slim

# Set environment variables
ENV FLASK_APP=app.py
ENV VENV_DIR="/opt/venv"
ENV LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"

ENV MAIL_USE_TLS=False
ENV MAIL_USE_SSL=True

RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat \    
    python3 \
    python3-venv \
    python3-pip \
    postgresql-client \
    zlib1g-dev \
    libpq-dev \
    git \
    sudo \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv $VENV_DIR

RUN $VENV_DIR/bin/pip install --upgrade pip

RUN $VENV_DIR/bin/pip install gunicorn

COPY requirements.txt . 
RUN $VENV_DIR/bin/pip install -r requirements.txt

ENV PATH="$VENV_DIR/bin:$PATH"

WORKDIR /home/qtrvsim-eval-web

COPY . /home/setup

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
