#!/bin/sh

# Зупиняємо скрипт, якщо якась команда впаде
set -e

# Чекаємо, поки база підніметься (необов'язково, але корисно)
# echo "Waiting for postgres..."

# Застосовуємо міграції
echo "Applying database migrations..."
flask db upgrade

# Запускаємо додаток
echo "Starting Flask..."

# Встановлюємо інструменти OTel (одноразово при запуску)
opentelemetry-bootstrap -a install

# Запускаємо додаток через OTel
exec opentelemetry-instrument python run.py
