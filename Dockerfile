ARG ARCH=

# Pull base image
FROM ubuntu:latest


# Labels
LABEL MAINTAINER="https://github.com/dbsqp/"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    tzdata \
    debian-archive-keyring

# Note fails for ARM, have removed arm build target from yml file


# Setup external package-sources
RUN apt-get update && apt-get install -y \
    python3 \
    python3-dev \
    python3-setuptools \
    python3-pip \
    python3-virtualenv \
    python3-venv \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/* 

# set venv
RUN python3 -m venv docker_env
RUN . docker_env/bin/activate

RUN python3 -m venv --system-site-packages /usr/local

# do pip installs 
RUN pip3 install pytz influxdb-client requests
#datetime json os subprocess time socket sys

# Environment vars
ENV PYTHONIOENCODING=utf-8

# Copy files
ADD skoda2influxdb.py /
ADD entrypoint.sh /

# Run
CMD ["/bin/bash","/entrypoint.sh"]
