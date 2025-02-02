FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-core \
    libreoffice-java-common \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    python3 \
    python3-pip \
    python3-virtualenv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN mkdir /app
COPY app.py /app/app.py

WORKDIR /app

RUN python3 -m virtualenv /venv
ENV PATH=/venv/bin:$PATH

RUN pip3 install flask

CMD ["/venv/bin/python", "app.py"]
