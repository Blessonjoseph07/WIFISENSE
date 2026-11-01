# The API in a container, for running the whole project locally with Docker (see docker-compose.yml and docs/DOCKER.md).
# Render does not use this file: render.yaml builds the API with Render's own Python runtime.
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first, so a code change does not reinstall them.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

# Run as a normal user; uploads are written to /app/uploads (a volume in docker-compose.yml).
RUN useradd --create-home --uid 1000 wifisense \
    && mkdir -p /app/uploads \
    && chown -R wifisense:wifisense /app
USER wifisense

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
