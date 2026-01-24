# Використовуємо легкий образ Python
FROM python:3.10-slim
# Встановлюємо робочу директорію всередині контейнера
WORKDIR /app

# Спочатку копіюємо requirements, щоб кешувати встановлення бібліотек
COPY requirements.txt requirements.txt

# Встановлюємо залежності
# libpq-dev потрібен для збірки psycopg2 (драйвер postgres)
RUN apt-get update && apt-get install -y libpq-dev gcc \
  && pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код проєкту
COPY . .

# Відкриваємо порт 5000
EXPOSE 5000

# Команда запуску
CMD ["python", "run.py"]
