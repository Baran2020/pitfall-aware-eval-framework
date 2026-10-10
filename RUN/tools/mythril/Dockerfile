FROM python:3.10-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    git build-essential curl \
    libssl-dev libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install mythril

RUN pip install solc-select && \
    solc-select install 0.4.24 && \
    solc-select use 0.4.24

# tolerant verify (myth version sometimes returns non-zero)
RUN solc --version && (myth version || true)

COPY toolwrapper_mythril.py /app/toolwrapper_mythril.py

# pass dataset path as argument to the wrapper
ENTRYPOINT []

