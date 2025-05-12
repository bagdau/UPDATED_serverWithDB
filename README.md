## Secure Async Document Server
## Асинхронный сервер с регистрацией, шифрованием, хешированием и очередями через FastAPI.

## Быстрый старт
bash
Копировать
Редактировать
# Клонируем и входим в каталог
cd путь/к/проекту

# Создаём окружение и активируем
python -m venv venv
source venv/bin/activate      # или venv\Scripts\activate (Windows)

# Устанавливаем зависимости
pip install -r requirements.txt

# Запуск (разработка)
uvicorn main:app --host 0.0.0.0 --port 5000 --reload

# Swagger: http://127.0.0.1:5000/docs
🛠 systemd (Linux)
ini
Копировать
Редактировать
[Unit]
Description=FastAPI Service
After=network.target

[Service]
User=ВАШ_ПОЛЬЗОВАТЕЛЬ
WorkingDirectory=/путь/к/проекту
ExecStart=/путь/к/проекту/venv/bin/uvicorn main:app --host 0.0.0.0 --port 5000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
bash
Копировать
Редактировать
sudo systemctl daemon-reload
sudo systemctl enable fastapi
sudo systemctl start fastapi
## Модуль db_core
Асинхронный доступ к SQLite через DBProducer (очередь + воркер). Поддерживает регистрацию, авторизацию, обновление данных, блокировки, восстановление пароля и резервные копии.

python
Копировать
Редактировать
## Пример
asyncio.create_task(DBWorker().run())
await DBProducer().add_user(login="...", password="...")
# Авторы: Бағдаулет Көптілеу и Аззамкулов Шахруз
Дата обновление: 2025-05-10  

