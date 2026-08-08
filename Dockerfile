FROM python:3.11-slim

WORKDIR /app

# Instala ferramentas básicas de build do Linux
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Garante a existência dos diretórios de dados e logs
RUN mkdir -p database logs

# Comando de inicialização otimizado apontando para o bot.py
CMD ["python", "bot.py"]
