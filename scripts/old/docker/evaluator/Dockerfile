FROM ubuntu:jammy

ENV VENV_DIR="/opt/venv"
ENV LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"

# Update, install necessary dependencies, and add sudo
RUN apt-get update && apt-get install -y --no-install-recommends \
	python3 \
	python3-venv \
	python3-pip \
	git \
	sudo \
	gnupg \
	software-properties-common \
	&& rm -rf /var/lib/apt/lists/*

# Add the GPG key for the qtrvsim PPA manually and install qtrvsim-cli
RUN sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 6ABE86107FE08A77 \
	&& sudo add-apt-repository ppa:qtrvsimteam/ppa \
	&& sudo apt-get update \
	&& sudo apt-get install -y qtrvsim \
	&& rm -rf /var/lib/apt/lists/*

# Create a virtual environment and upgrade pip
RUN python3 -m venv $VENV_DIR
RUN $VENV_DIR/bin/pip install --upgrade pip

# Install Python dependencies from requirements.txt
COPY requirements.txt . 
RUN $VENV_DIR/bin/pip install -r requirements.txt

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Expose the necessary port
EXPOSE 8080

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
