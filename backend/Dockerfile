FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependências de sistema. As ferramentas de recon (subfinder, httpx, nmap)
# são adicionadas nas Fases 2-4 na imagem do worker.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python a partir do pyproject (camada cacheável).
COPY pyproject.toml ./
COPY app ./app
RUN pip install .

# Usuário não-root.
RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
