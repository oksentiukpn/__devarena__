FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# add execute permissions
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 5000

# Run script to run app
ENTRYPOINT ["/app/entrypoint.sh"]
