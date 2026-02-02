FROM python:3.10-slim

RUN useradd --user-group --system --no-create-home appuser


WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc \
  && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# add execute permissions
RUN chmod +x /usr/local/bin/entrypoint.sh && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Run script to run app
ENTRYPOINT ["entrypoint.sh"]
