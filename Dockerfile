FROM python:3.12-slim

# 1. crear directorio
WORKDIR /app

# 2. instalar dependencias de sistema (para mysqlclient/pymysql casi no hace falta, pero dejamos básicos)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# 3. copiar requirements
COPY requirements.txt ./

# 4. instalar
RUN pip install --no-cache-dir -r requirements.txt

# 5. copiar el código
COPY . .

# 6. exponer puerto
EXPOSE 8000

# 7. comando
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
