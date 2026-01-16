FROM debian:trixie

RUN apt-get update && \
	apt-get install -y \
	systemd \
	systemd-sysv \
	sudo \
	&& rm -rf /var/lib/apt/lists/*

COPY . /opt/qtrvsim-eval-web/

WORKDIR /opt/qtrvsim-eval-web

ENTRYPOINT ["/lib/systemd/systemd"]
