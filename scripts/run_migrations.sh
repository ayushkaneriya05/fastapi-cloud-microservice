#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
alembic revision --autogenerate 
alembic upgrade head
