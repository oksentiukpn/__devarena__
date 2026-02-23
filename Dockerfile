# Build CSS
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY app/templates/ ./app/templates/
COPY app/static/src/ ./app/static/src/
RUN npm run build

# Python image
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend-builder /app/app/static/css/output.css ./app/static/css/output.css
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# add execute permissions
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 5000

# Run script to run app
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
