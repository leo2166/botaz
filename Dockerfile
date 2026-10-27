FROM node:20-bookworm-slim AS node_base

FROM python:3.11-slim-bookworm

# Instalar dependencias del sistema requeridas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copiar Node.js y npm desde node_base
COPY --from=node_base /usr/local/bin/node /usr/local/bin/node
COPY --from=node_base /usr/local/include/node /usr/local/include/node
COPY --from=node_base /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

WORKDIR /app

# 1. Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Instalar dependencias de Node.js en gateway
COPY gateway/package*.json ./gateway/
RUN cd gateway && npm ci --omit=dev

# 3. Copiar código fuente
COPY . .

# Limpieza de saltos de línea Windows (CRLF a LF) y permisos de ejecución
RUN sed -i 's/\r$//' start.sh && chmod +x start.sh

# Variables de entorno por defecto
ENV PORT=8000
ENV GATEWAY_PORT=3001
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["./start.sh"]
