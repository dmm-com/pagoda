FROM node:18.12

# hadolint ignore=DL3013, DL3008
RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
    screen \
    sudo \
    vim \
    && apt-get upgrade --yes \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Make the user ID the same to share the directory with the host OS
ARG USER_ID=1000
RUN echo "#$USER_ID ALL=NOPASSWD: ALL" > /etc/sudoers.d/airone
RUN getent passwd $USER_ID || useradd -u $USER_ID -m -s /bin/bash airone
USER $USER_ID
WORKDIR /airone
