FROM continuumio/miniconda3:latest
WORKDIR /app
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*
RUN conda create -n tf31 python=3.6 -y && \
    conda run -n tf31 pip install --no-cache-dir \
        tensorflow==1.13.1 keras==2.2.4 pandas scikit-learn "numpy<1.17" "h5py==2.10.0" \
        "gensim==3.8.3" "smart_open==1.10.0" matplotlib
COPY . /app