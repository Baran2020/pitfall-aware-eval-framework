FROM continuumio/miniconda3:latest
WORKDIR /app
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*
RUN conda config --set channel_priority strict
RUN conda create -n tf29 python=3.9 -y && \
    conda install -n tf29 -y -c conda-forge "tensorflow=2.9.*" && \
    conda install -n tf29 -y -c conda-forge numpy=1.25.2 scipy=1.9.3 pandas scikit-learn matplotlib gensim && \
    conda run -n tf29 pip install --no-cache-dir py-solc-x pyevmasm
COPY . /app