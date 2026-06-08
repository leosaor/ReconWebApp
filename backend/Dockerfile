FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Dependencias de sistema + ferramentas de recon.
ARG SUBFINDER_VERSION=2.6.6
ARG HTTPX_VERSION=1.9.0
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    dnsutils \
    nmap \
    unzip \
    && curl -sSL -o /tmp/subfinder.zip \
       https://github.com/projectdiscovery/subfinder/releases/download/v${SUBFINDER_VERSION}/subfinder_${SUBFINDER_VERSION}_linux_amd64.zip \
    && unzip /tmp/subfinder.zip -d /usr/local/bin subfinder \
    && chmod +x /usr/local/bin/subfinder \
    && curl -sSL -o /tmp/httpx.zip \
       https://github.com/projectdiscovery/httpx/releases/download/v${HTTPX_VERSION}/httpx_${HTTPX_VERSION}_linux_amd64.zip \
    && unzip /tmp/httpx.zip -d /usr/local/bin httpx \
    && chmod +x /usr/local/bin/httpx \
    && rm /tmp/subfinder.zip /tmp/httpx.zip \
    && apt-get purge -y unzip \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Instala dependencias Python a partir do pyproject (camada cacheavel).
COPY pyproject.toml ./
COPY app ./app
RUN pip install . \
    && playwright install chromium --with-deps \
    && chmod -R 755 /ms-playwright

# Usuario nao-root.
RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
