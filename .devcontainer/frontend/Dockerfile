FROM node:18.12-bullseye

RUN apt-get update \
    && apt-get install -y \
    sudo

ARG USER_ID=1000
RUN getent passwd $USER_ID || useradd -u $USER_ID -m -s /bin/bash airone
RUN echo "#$USER_ID ALL=NOPASSWD: ALL" > /etc/sudoers.d/airone
