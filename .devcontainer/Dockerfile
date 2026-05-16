FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# git já vem na imagem base

# Python 3.12
RUN echo "Installing Python 3.12..." \
    && apt-get update && apt-get install -y python3.12 python3.12-venv python3.12-dev python3-pip \
    && ln -sf /usr/bin/python3.12 /usr/local/bin/python3 \
    && ln -sf /usr/bin/python3.12 /usr/local/bin/python \
    && rm -rf /var/lib/apt/lists/*

# Node 20
RUN echo "Installing Node.js..." \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

USER vscode

# Instalação do Claude CLI
RUN echo "Installing Claude CLI..." \
    && curl -fsSL https://claude.ai/install.sh | bash

USER root