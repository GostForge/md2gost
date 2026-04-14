FROM python:3.11-slim

WORKDIR /app

# System deps for python-docx, freetype, pillow and strict MS font setup.
RUN set -eux; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i \
        's/^Components: .*/Components: main contrib non-free non-free-firmware/' \
        /etc/apt/sources.list.d/debian.sources; \
    elif [ -f /etc/apt/sources.list ]; then \
      sed -i 's/ main$/ main contrib non-free non-free-firmware/' /etc/apt/sources.list; \
    fi; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      ca-certificates libfreetype6 libfreetype6-dev fontconfig gcc \
      debconf-utils cabextract wget xfonts-utils fontforge; \
    echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections; \
    apt-get install -y --no-install-recommends ttf-mscorefonts-installer; \
    wget -q https://gist.githubusercontent.com/maxwelleite/10774746/raw/ttf-vista-fonts-installer.sh -O /tmp/vista.sh; \
    bash /tmp/vista.sh; \
    rm -f /tmp/vista.sh; \
    fc-cache -f; \
    for family in "Times New Roman" "Courier New" "Calibri" "Consolas"; do \
      resolved_family="$(fc-match --format='%{family}\n' "${family}:weight=regular:slant=roman")"; \
      echo "${family} -> ${resolved_family}"; \
      if ! printf '%s' "${resolved_family}" | tr ',' '\\n' | grep -Fxqi "${family}"; then \
        echo "Required font '${family}' is not resolved exactly" >&2; \
        exit 1; \
      fi; \
    done; \
    rm -rf /var/lib/apt/lists/*; \
    pip install --no-cache-dir poetry

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
