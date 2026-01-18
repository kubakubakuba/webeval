FROM debian:trixie

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
	python3 \
	python3-pip \
	make \
	gcc \
	g++ \
	gcc-riscv64-unknown-elf \
	qtrvsim \
	&& rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
	toml \
	markdown \
	psycopg2-binary \
	python-dotenv

COPY evaluator/ /app/

COPY docker/evaluator/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
