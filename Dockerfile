FROM python:3.11-slim

WORKDIR /app

# System deps for python-docx, freetype, pillow and font discovery (fc-list)
RUN apt-get update && apt-get install -y --no-install-recommends \
  libfreetype6 libfreetype6-dev fontconfig fonts-dejavu-core gcc && \
    rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --no-cache-dir poetry

# Copy project definition
COPY pyproject.toml poetry.lock* ./

# Reconcile lock file and install dependencies (without dev deps)
RUN poetry config virtualenvs.create false && \
  poetry lock --no-interaction && \
  poetry install --no-interaction --no-ansi --no-root --only main

# Copy source
COPY md2gost/ md2gost/
COPY README.md ./

# Install package itself
RUN poetry install --no-interaction --no-ansi --only-root

ENV MD2GOST_HOST=0.0.0.0
ENV MD2GOST_PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "md2gost.server"]
