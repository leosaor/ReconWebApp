FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1     PYTHONDONTWRITEBYTECODE=1     PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias de sistema + subfinder (Phase 2)
ARG SUBFINDER_VERSION=2.6.6
RUN apt-get update && apt-get install -y --no-install-recommends     curl     unzip     ca-certificates     && curl -sSL -o /tmp/subfinder.zip        https://github.com/projectdiscovery/subfinder/releases/download/v${SUBFINDER_VERSION}/subfinder_${SUBFINDER_VERSION}_linux_amd64.zip     && unzip /tmp/subfinder.zip -d /usr/local/bin subfinder     && chmod +x /usr/local/bin/subfinder     && rm /tmp/subfinder.zip     && apt-get purge -y unzip && apt-get autoremove -y     && rm -rf /var/lib/apt/lists/*

# Instala dependencias Python a partir do pyproject (camada cacheavel).
COPY pyproject.toml ./
COPY app ./app
RUN pip install .

# Usuario nao-root.
RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
