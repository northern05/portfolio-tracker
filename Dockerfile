FROM python:3.11

RUN apt-get update && apt-get upgrade -y && apt-get install -y chromium-driver
RUN pip install --upgrade pip

# Install Node.js v20.10.0
ENV NVM_DIR=/root/.nvm
ENV NODE_VERSION=20.18.0

RUN curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash && \
    export NVM_DIR=$NVM_DIR && \
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && \
    nvm install $NODE_VERSION && \
    nvm alias default $NODE_VERSION && \
    nvm use default

ENV NODE_PATH=$NVM_DIR/versions/node/v$NODE_VERSION/lib/node_modules
ENV PATH=$NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH

WORKDIR /usr/src/app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --force-reinstall -r requirements.txt

COPY . /usr/src/app/

WORKDIR /usr/src/app/raydiumSwap

RUN corepack enable && yarn set version stable && \
    yarn config set nodeLinker node-modules && \
    yarn install && \
    yarn add ts-node @solana/web3.js

WORKDIR /usr/src/app