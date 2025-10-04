#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$ROOT_DIR"

PORT="${PORT:-8000}"
APP_IMPORT_PATH="${APP_IMPORT_PATH:-app.main:app}"

# shellcheck disable=SC1091
source .venv/bin/activate

exec uvicorn "$APP_IMPORT_PATH" --reload --port "$PORT"
