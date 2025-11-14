FROM ubuntu:jammy

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
	python3 \
	python3-pip \
	gnupg \
	software-properties-common \
	&& apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 6ABE86107FE08A77 \
	&& add-apt-repository ppa:qtrvsimteam/ppa \
	&& apt-get update \
	&& apt-get install -y qtrvsim \
	&& rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --upgrade pip && \
	pip3 install --no-cache-dir \
	toml \
	markdown \
	psycopg2-binary \
	python-dotenv

COPY evaluator/ /app/

COPY docker/evaluator/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
