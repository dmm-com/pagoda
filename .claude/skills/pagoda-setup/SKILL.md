---
name: pagoda-setup
description: |
  Automates and guides the initial environment setup for the Pagoda/AirOne project. Covers Python, Node.js, Docker, MySQL, Elasticsearch, RabbitMQ setup, dependency installation, DB migration, user creation, and frontend build in a single flow. Trigger on requests like "set up the environment", "setup", "initial configuration", "I want to set up a dev environment", "get it running", "install", "getting started", or whenever a new developer needs to get the project running for the first time.
---

# Pagoda Initial Environment Setup Guide

This skill sets up the Pagoda/AirOne development environment from scratch. It selects the appropriate path (DevContainer / baremetal / Docker) based on the user's environment and automates as much as possible.

## Initial Questions

Ask the user the following to choose the right setup path:

1. **Development style**: Use DevContainer (VS Code) or build directly on the local machine?
2. **Docker availability**: Are `docker` and `docker compose` available?
3. **OS**: macOS / Linux / WSL? (affects how dependencies are installed)

## Setup Path A: DevContainer (Recommended)

The simplest approach. Requires only VS Code + Docker Desktop.

### Steps

1. Run "Reopen in Container" in VS Code
2. After container build, `uv sync --extra dev && npm install` runs automatically (postCreateCommand)
3. Proceed to "Common: DB and Service Initialization"

DevContainer automatically starts MySQL, Elasticsearch, and RabbitMQ via `.devcontainer/docker-compose.yml`. Environment variables are pre-configured.

## Setup Path B: Local Build (Baremetal)

### Prerequisites Check and Installation

The following tools are required. Check each tool's version and guide installation for any that are missing.

| Tool | Required Version | Check Command |
|------|-----------------|---------------|
| Python | 3.12.9 | `python3 --version` |
| Node.js | 22.13.1 | `node --version` |
| uv | latest | `uv --version` |
| Docker + Compose | latest | `docker --version && docker compose version` |

**Installing Python (if missing):**
```bash
# macOS (pyenv recommended)
brew install pyenv
pyenv install 3.12.9
pyenv local 3.12.9

# Or use mise/asdf
```

**Installing Node.js (if missing):**
```bash
# macOS (nodenv / nvm / mise recommended)
brew install nodenv
nodenv install 22.13.1
nodenv local 22.13.1
```

**Installing uv (if missing):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install Dependencies

```bash
# Backend
uv sync --extra dev

# Frontend
npm install
```

### Start Middleware

Start middleware services via Docker Compose:

```bash
docker compose up -d
```

This starts:
- **MySQL 8.0.36** — port 3306 (no authentication, utf8mb4)
- **Elasticsearch 8.17.0** — port 9200 (security disabled, single-node)
- **RabbitMQ 4.1.3** — port 5672 (AMQP) + 15672 (management UI, guest/guest)

### Configure Environment Variables

Create a `.env` file in the project root. Django auto-reads it via `django-environ`.

**Minimal configuration (values matching Docker Compose defaults):**

```
AIRONE_MYSQL_MASTER_URL=mysql://root:@127.0.0.1:3306/airone?charset=utf8mb4
AIRONE_ELASTICSEARCH_URL=elasticsearch://airone:password@localhost:9200/airone
AIRONE_RABBITMQ_URL=amqp://guest:guest@localhost//
AIRONE_SECRET_KEY=dev-secret-key-change-in-production
AIRONE_DEBUG=true
```

Note: The `.env` file contains sensitive information and must never be read directly. Ask the user to create it and have them enter the values themselves.

## Common: DB and Service Initialization

### Verify Middleware is Running

Before initialization, confirm each service is up:

```bash
# MySQL
docker compose exec mysql mysqladmin ping -h localhost

# Elasticsearch
curl -s http://localhost:9200/_cluster/health | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])"

# RabbitMQ
curl -s -u guest:guest http://localhost:15672/api/overview | python3 -c "import sys,json; print('OK')"
```

### DB Initialization and Migration

```bash
# Baremetal (-b flag)
./tools/clear_and_initdb.sh -b

# DevContainer / inside Docker
./tools/clear_and_initdb.sh
```

This script performs:
1. Create database (drops and recreates if it exists)
2. `makemigrations` — generate migration files
3. `migrate` — create tables
4. Create the auto_complementer user

### Create Admin User

```bash
./tools/register_user.sh -s -p <password> <username>
```

Ask the user for the password and username before running. `-s` grants superuser privileges.

### Build Frontend

```bash
npm run build
```

For development, use watch mode for auto-rebuild on changes:
```bash
npm run watch
```

### Verify Everything Works

```bash
# Django development server
uv run python manage.py runserver

# In a separate terminal, start Celery worker (for async jobs)
uv run celery -A airone worker -l info
```

Access http://localhost:8000/ in a browser to verify.

## Troubleshooting

### mysqlclient build error (macOS)

```bash
# If mysql_config is not found
brew install mysql-client pkg-config
export PKG_CONFIG_PATH="$(brew --prefix mysql-client)/lib/pkgconfig"
uv sync --extra dev
```

### Elasticsearch won't start

```bash
# If memory is insufficient (check Docker Desktop allocation)
# If vm.max_map_count is too low (Linux)
sudo sysctl -w vm.max_map_count=262144
```

### npm install GitHub Packages authentication error

`.npmrc` references the GitHub Packages registry. A GitHub token may be required to fetch `@dmm-com` scoped packages:

```bash
npm login --registry=https://npm.pkg.github.com
```

### python-ldap / python3-saml build error

```bash
# macOS
brew install openldap libxml2 xmlsec1
export LDFLAGS="-L$(brew --prefix openldap)/lib"
export CPPFLAGS="-I$(brew --prefix openldap)/include"
```

## Automation Policy

Automate as much as possible. However, always confirm with the user before:

- Creating the `.env` file (sensitive values must be entered by the user)
- Dropping and recreating the DB (existing data will be lost)
- Starting Docker Compose (potential port conflicts)
- Setting username and password

Explain what each step does before executing. If an error occurs, diagnose the cause and suggest a fix. Proceed step by step without skipping.
