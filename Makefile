.PHONY: up down dev test lint migrate shell-api shell-worker logs

# Sobe os serviços de desenvolvimento (sem nginx)
up:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Sobe em background
up-d:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

# Sobe com nginx (produção local)
up-prod:
	docker compose --profile prod up --build -d

# Para tudo
down:
	docker compose down

# Para tudo e remove volumes (cuidado: apaga dados do banco)
down-clean:
	docker compose down -v

# Roda os testes do backend dentro do container
test:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm api \
		sh -c "pip install -q '.[dev]' && pytest"

# Lint do backend
lint:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm api \
		sh -c "pip install -q '.[dev]' && ruff check app && black --check app"

# Roda migrations pendentes
migrate:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm api \
		alembic upgrade head

# Gera nova migration (use: make migration MSG="descricao")
migration:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm api \
		alembic revision --autogenerate -m "$(MSG)"

# Abre shell no container da API
shell-api:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml exec api bash

# Abre shell no worker
shell-worker:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml exec worker bash

# Logs em tempo real
logs:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f
