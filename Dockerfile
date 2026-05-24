FROM python:3.12-slim

# Dependências de sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    poppler-utils \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código (baml_client já está commitado — não precisa gerar)
COPY . .

# Verifica que o baml_client está ok
RUN python -c "from baml_client.sync_client import b; print('baml_client ok')"

# Verifica que o agente importa corretamente
RUN python -c "from agent import processar_narrativa; print('agent ok')"

# Porta dinâmica (Railway injeta PORT via env)
# Não hardcodar EXPOSE — Railway injeta PORT em tempo de run
CMD ["python", "main.py"]
