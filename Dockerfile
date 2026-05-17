FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1     HINDSIGHT_API_HOST=0.0.0.0     HINDSIGHT_API_PORT=8888     HINDSIGHT_API_LOG_LEVEL=info     HINDSIGHT_API_RUN_MIGRATIONS_ON_STARTUP=true

RUN apt-get update     && apt-get install -y --no-install-recommends build-essential curl     && pip install --upgrade pip     && pip install "hindsight-all"     && apt-get purge -y --auto-remove build-essential     && rm -rf /var/lib/apt/lists/*

EXPOSE 8888

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5   CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8888/health', timeout=3).read()"

CMD ["python", "-m", "hindsight_api.main", "--host", "0.0.0.0", "--port", "8888", "--no-access-log"]
