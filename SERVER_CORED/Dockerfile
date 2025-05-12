# 1. Базалық имидж — ең минималды әрі сенімді
FROM python:3.11-slim

# 2. Жұмыс директориясы
WORKDIR /app

# 3. Копируем файлдар
COPY requirements.txt .

# 4. Тәуелділіктерді орнатамыз
RUN pip install --no-cache-dir -r requirements.txt

# 5. Flask сервер кодын көшіреміз
COPY . .

# 6. Порт ашамыз (мысалы, 5000 порт Flask үшін)
EXPOSE 5000

# 7. Фласк қосымшасын іске қосамыз
CMD ["python", "app.py"]
