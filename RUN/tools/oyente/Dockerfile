FROM hrishioa/oyente:latest
WORKDIR /app

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys B50ABD2EE384B7D4 || true && \
    apt-get update && apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# solc 0.4.25 (compatible with ^0.4.x pragmas in dataset)
COPY solc /usr/local/bin/solc
RUN chmod +x /usr/local/bin/solc && solc --version

# Wrap disasm to strip swarm hash (prevents panic with solc >= 0.4.7)
COPY disasm_wrapper.sh /tmp/disasm_wrapper.sh
RUN mv /usr/bin/disasm /usr/bin/disasm.real && \
    cp /tmp/disasm_wrapper.sh /usr/bin/disasm && \
    chmod +x /usr/bin/disasm

# Z3 setup
RUN cp /home/oyente/dependencies/z3-z3-4.4.1/build/z3 /usr/local/bin/z3 && \
    chmod +x /usr/local/bin/z3 && \
    cp /home/oyente/dependencies/z3-z3-4.4.1/build/libz3.so /usr/lib/ && \
    ldconfig && \
    Z3_BUILD=/home/oyente/dependencies/z3-z3-4.4.1/build && \
    for f in z3.py z3core.py z3types.py z3util.py z3consts.py z3printer.py; do \
        ln -sf $Z3_BUILD/$f /usr/lib/python2.7/$f; \
    done

# Python 3 conversion
RUN cp -r /home/oyente/oyente /home/oyente/oyente3 && \
    (2to3 -w /home/oyente/oyente3/ || python3 -m lib2to3 -w /home/oyente/oyente3/) && \
    Z3_BUILD=/home/oyente/dependencies/z3-z3-4.4.1/build && \
    for f in z3.py z3core.py z3types.py z3util.py z3consts.py z3printer.py; do \
        ln -sf $Z3_BUILD/$f /home/oyente/oyente3/$f; \
    done && \
    ln -sf /home/oyente/dependencies/z3-z3-4.4.1/build/libz3.so /home/oyente/oyente3/libz3.so

COPY fix_oyente3.py /tmp/fix_oyente3.py
RUN python3 /tmp/fix_oyente3.py

# Patch python2 calls + subprocess text mode in oyente3
COPY patch_oyente3.py /tmp/patch_oyente3.py
RUN python3 /tmp/patch_oyente3.py

COPY toolwrapper_oyente.py /app/toolwrapper_oyente.py
ENTRYPOINT []
#ENTRYPOINT ["python3", "/app/toolwrapper_oyente.py"]