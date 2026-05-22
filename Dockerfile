FROM python:3.12-slim

ARG HINDSIGHT_VERSION=0.6.2

ENV PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1     HINDSIGHT_API_HOST=0.0.0.0     HINDSIGHT_API_PORT=8888     HINDSIGHT_API_LOG_LEVEL=info     HINDSIGHT_API_RUN_MIGRATIONS_ON_STARTUP=true

RUN apt-get update     && apt-get install -y --no-install-recommends build-essential curl     && pip install --upgrade pip     && pip install "hindsight-all==${HINDSIGHT_VERSION}"     && apt-get purge -y --auto-remove build-essential     && rm -rf /var/lib/apt/lists/*

# Temporary hotfix for Hindsight 0.6.2: acquire_with_retry must retry only
# connection acquisition, not exceptions raised by caller code using the
# yielded connection. Without this, operation timeouts can become
# "RuntimeError: generator didn't stop after athrow()".
COPY patches/hindsight_api/engine/db_utils.py /tmp/hindsight_db_utils.py
RUN python -c "import pathlib, shutil, hindsight_api.engine.db_utils as db_utils; shutil.copyfile('/tmp/hindsight_db_utils.py', pathlib.Path(db_utils.__file__))"

EXPOSE 8888

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5   CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8888/health', timeout=3).read()"

CMD ["python", "-m", "hindsight_api.main", "--host", "0.0.0.0", "--port", "8888", "--no-access-log"]
