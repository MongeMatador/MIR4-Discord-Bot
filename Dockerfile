FROM python:3.11-slim

WORKDIR /app

# Instala ferramentas essenciais do SO Linux para compilação C do Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Garante que os diretórios necessários existem no contêiner
RUN mkdir -p database logs

CMD ["python", "bot.py"]
