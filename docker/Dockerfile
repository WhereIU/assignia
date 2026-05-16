FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    netcat-openbsd \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID assignia && useradd -m -u $UID -g $GID assignia

# Даёт полные права на запись в /app для всех (только для локальной разработки)
RUN chmod 777 /app
RUN chown -R assignia:assignia /app

USER assignia