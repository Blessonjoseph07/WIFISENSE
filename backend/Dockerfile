# The API in a container. Render builds the hosted API from this file (render.yaml, runtime: docker), and docker-compose.yml
# uses it to run the whole project locally (see docs/DOCKER.md).
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

# Render tells the container which port to listen on in $PORT; locally it is unset and 8000 is used.
ENV PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import os,urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:' + os.environ['PORT'] + '/health', timeout=4).status == 200 else 1)"

# exec, so uvicorn receives the stop signal directly and shuts down cleanly on a redeploy.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
