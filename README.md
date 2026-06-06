# ReconWebApp

Plataforma web de **reconhecimento automatizado para pentest**, para uso de um time
em engajamentos **autorizados**. Arquitetura **API-first**: a interface web e a futura
CLI são clientes da mesma API.

> ⚠️ **Aviso legal:** esta ferramenta destina-se exclusivamente a testes de segurança
> em alvos para os quais exista **autorização por escrito**. O uso contra sistemas sem
> autorização é ilegal e de inteira responsabilidade do operador.

## Stack

| Camada | Tecnologia |
|---|---|
| Backend / API | FastAPI (Python 3.12), Pydantic v2, SQLAlchemy 2.0 + Alembic |
| Jobs assíncronos | Celery + Redis |
| Banco de dados | PostgreSQL |
| Frontend | Next.js (App Router) + React + TypeScript + Tailwind |
| Reverse proxy / TLS | Nginx |
| Deploy | Docker Compose |

## Módulos de recon (v1)

1. Enumeração de subdomínios — `subfinder`
2. HTTP probing + fingerprint — `httpx`
3. Port scanning + detecção de serviço/versão — `nmap` (`-sT -sV` por padrão)

Recon de rede adicional entra incrementalmente nas próximas versões.

## Autenticação e autorização

- Multi-usuário com RBAC (`admin` / `pentester` / `viewer`).
- Cada usuário vê apenas os **seus próprios projetos**; o `admin` vê todos.
- API keys por usuário (base para a futura CLI e rastreabilidade).

## Status

🚧 Em desenvolvimento — Fase 0 (scaffolding).

## Desenvolvimento

Instruções de setup local e deploy serão adicionadas junto da Fase 0.
