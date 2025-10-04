# Crear/activar venv
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

# Instalar requirements
pip install --upgrade pip
pip install -r requirements.txt

# Correr
uvicorn app.main:app --reload --port 8000
