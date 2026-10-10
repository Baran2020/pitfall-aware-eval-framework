FROM python:3.8-slim

RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    build-essential \
    curl

RUN python -m venv /opt/manticore-env
ENV PATH="/opt/manticore-env/bin:$PATH"

RUN pip install --upgrade pip


RUN pip install manticore==0.3.7 protobuf==3.20.3

# Manticore's Solidity front-end shells out to a plain `solc` on PATH (via
# crytic-compile) -- nothing above installs one, so every compile attempt
# failed with "No such file or directory: 'solc'". This was previously
# masked by the wrapper's invalid --quick-mode flag, which made every
# manticore invocation fail at argument-parsing time (before it ever tried
# to compile anything), so the missing-solc error never surfaced.
RUN pip install solc-select \
    && solc-select install 0.4.24 \
    && solc-select use 0.4.24

WORKDIR /app
COPY . .

CMD []