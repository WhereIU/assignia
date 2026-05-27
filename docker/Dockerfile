FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    netcat-openbsd \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID assignia && useradd -m -u $UID -g $GID assignia

COPY ./app /app

RUN chown -R assignia:assignia /app

USER assignia