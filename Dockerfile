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
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# Даємо права і прибираємо можливі Windows-символи (\r), якщо ти писав код на Windows
RUN chmod +x /usr/local/bin/entrypoint.sh && sed -i 's/\r$//' /usr/local/bin/entrypoint.sh
#
EXPOSE 5000
#
# # Запускаємо скрипт з системної папки
ENTRYPOINT ["entrypoint.sh"]
