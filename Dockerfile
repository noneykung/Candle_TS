FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY candle ./candle
RUN pip install --no-cache-dir . && rm -rf candle pyproject.toml build

RUN useradd --create-home candle && mkdir -p /app/data && chown candle /app/data
USER candle

ENV PYTHONUNBUFFERED=1 \
    DB_PATH=/app/data/candle.db

CMD ["python", "-m", "candle"]
