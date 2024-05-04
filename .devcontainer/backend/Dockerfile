FROM python:3.11-bullseye

RUN apt-get update \
    && apt-get install -y \
    libldap2-dev \
    libsasl2-dev \
    libxmlsec1-dev \
    default-mysql-client \
    default-libmysqlclient-dev \
    sudo

RUN pip install --no-cache-dir --upgrade \
    pip \
    poetry

ARG USER_ID=1000
RUN getent passwd $USER_ID || useradd -u $USER_ID -m -s /bin/bash airone
RUN echo "#$USER_ID ALL=NOPASSWD: ALL" > /etc/sudoers.d/airone
