FROM python:3.11-slim

WORKDIR /app

# Копируем все файлы бота
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]