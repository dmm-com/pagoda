FROM python:3.11-bullseye

ENV TZ Asia/Tokyo
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y \
    sudo \
    vim \
    # required for airone library
    libldap2-dev \
    libsasl2-dev \
    libxmlsec1-dev \
    default-mysql-client \
    default-libmysqlclient-dev

ARG USER_ID=1000
RUN getent passwd $USER_ID || useradd -u $USER_ID -m -s /bin/bash airone
RUN echo "#$USER_ID ALL=NOPASSWD: ALL" > /etc/sudoers.d/airone
USER $USER_ID

# nodenv, node
COPY .node-version ./
RUN curl -fsSL https://github.com/nodenv/nodenv-installer/raw/HEAD/bin/nodenv-installer | bash
RUN echo 'export PATH="$HOME/.nodenv/bin:$PATH"' >> ~/.profile
RUN echo 'eval "$(nodenv init -)"' >> ~/.profile
RUN bash -c '\
    export PATH="$HOME/.nodenv/bin:$PATH"; \
    eval "$(nodenv init -)"; \
    nodenv install'

# python
RUN pip install --no-cache-dir --upgrade \
    pip \
    poetry
