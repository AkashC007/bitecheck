FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY apps/api/pyproject.toml apps/api/README.md ./apps/api/
COPY apps/api/src ./apps/api/src
COPY config ./config
COPY data ./data

RUN python -m pip install --no-cache-dir ./apps/api

EXPOSE 8000

CMD ["sh", "-c", "uvicorn --app-dir apps/api/src bitecheck_api.main:app --host 0.0.0.0 --port ${PORT}"]
