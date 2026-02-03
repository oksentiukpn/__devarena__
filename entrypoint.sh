#!/bin/sh

# Зупиняємо скрипт, якщо якась команда впаде
set -e

# Чекаємо, поки база підніметься (необов'язково, але корисно)
# echo "Waiting for postgres..."

# Застосовуємо міграції
echo "Applying database migrations..."
flask db migrate
flask db upgrade

# Запускаємо додаток
echo "Starting Flask..."
exec python run.py
