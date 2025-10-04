#!/usr/bin/env bash
set -euo pipefail

# directorio del repo (raíz)
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$ROOT_DIR"

PY_BIN="${PY_BIN:-python3}"

echo "==> Using Python: $($PY_BIN --version || echo 'not found')"

# 1) crear venv si no existe
if [ ! -d ".venv" ]; then
  echo "==> Creating virtualenv .venv"
  $PY_BIN -m venv .venv
fi

# 2) activar venv
# shellcheck disable=SC1091
source .venv/bin/activate

# 3) actualizar pip
python -m pip install --upgrade pip wheel setuptools

# 4) instalar requirements
REQ_FILES=("requirements.txt" "requirements2.txt")
for f in "${REQ_FILES[@]}"; do
  if [ -f "$f" ]; then
    echo "==> Installing $f"
    pip install -r "$f"
  fi
done

echo "==> Done. To activate: source .venv/bin/activate"
