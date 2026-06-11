FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Dependencias de sistema + ferramentas de recon.
ARG SUBFINDER_VERSION=2.6.6
ARG HTTPX_VERSION=1.9.0
ARG FEROXBUSTER_VERSION=2.13.0
ARG NUCLEI_VERSION=3.8.0
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    dnsutils \
    git \
    nmap \
    sslscan \
    unzip \
    && curl -sSL -o /tmp/subfinder.zip \
       https://github.com/projectdiscovery/subfinder/releases/download/v${SUBFINDER_VERSION}/subfinder_${SUBFINDER_VERSION}_linux_amd64.zip \
    && unzip /tmp/subfinder.zip -d /usr/local/bin subfinder \
    && chmod +x /usr/local/bin/subfinder \
    && curl -sSL -o /tmp/httpx.zip \
       https://github.com/projectdiscovery/httpx/releases/download/v${HTTPX_VERSION}/httpx_${HTTPX_VERSION}_linux_amd64.zip \
    && unzip /tmp/httpx.zip -d /usr/local/bin httpx \
    && chmod +x /usr/local/bin/httpx \
    && curl -sSL -o /tmp/feroxbuster.tar.gz \
       https://github.com/epi052/feroxbuster/releases/download/v${FEROXBUSTER_VERSION}/x86_64-linux-feroxbuster.tar.gz \
    && tar -xzf /tmp/feroxbuster.tar.gz -C /usr/local/bin feroxbuster \
    && chmod +x /usr/local/bin/feroxbuster \
    && curl -sSL -o /tmp/nuclei.zip \
       https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}/nuclei_${NUCLEI_VERSION}_linux_amd64.zip \
    && unzip /tmp/nuclei.zip -d /usr/local/bin nuclei \
    && chmod +x /usr/local/bin/nuclei \
    && rm /tmp/subfinder.zip /tmp/httpx.zip /tmp/feroxbuster.tar.gz /tmp/nuclei.zip \
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
