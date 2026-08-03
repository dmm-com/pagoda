FROM python:3.13-bookworm

ENV TZ Asia/Tokyo
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y \
    sudo \
    vim \
    gh \
    # required for openapi-generator-cli (npm wrapper runs the Java jar)
    default-jre \
    # required for airone library
    libldap2-dev \
    libsasl2-dev \
    libxmlsec1-dev \
    default-mysql-client \
    default-libmysqlclient-dev

ARG USER_ID=1000
RUN getent passwd $USER_ID || useradd -u $USER_ID -m -s /bin/bash airone
RUN echo "#$USER_ID ALL=NOPASSWD: ALL" > /etc/sudoers.d/airone

# Paths that .devcontainer/docker-compose.yml mounts as named volumes have to
# exist here with the right ownership: Docker seeds an empty named volume from
# the image, and creates a root-owned directory when the path is missing.
RUN mkdir -p \
    /workspace/airone/.venv \
    /workspace/airone/node_modules \
    /home/airone/.cache/uv \
    /home/airone/.npm \
    /home/airone/.cache/ms-playwright \
    && chown -R $USER_ID:$USER_ID /workspace /home/airone

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
    uv
