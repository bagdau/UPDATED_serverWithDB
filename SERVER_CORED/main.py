
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from contextlib import asynccontextmanager
from modules.db_core import DBProducer, DBWorker
import sqlite3
import os
import asyncio

# --- БД: Добавляем колонку is_deleted, если её нет ---
conn = sqlite3.connect("users.db")
try:
    conn.execute("ALTER TABLE users ADD COLUMN is_deleted INTEGER DEFAULT 0;")
except sqlite3.OperationalError:
    pass  # Колонка уже существует
conn.commit()
conn.close()

# --- Конфигурация ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    worker = DBWorker(db_path=DB_PATH)
    task = asyncio.create_task(worker.run())
    app.state.db_producer = DBProducer()
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Главная страница админки ---
@app.get("/", response_class=HTMLResponse)
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT * FROM users WHERE is_deleted=0")
        users = cursor.fetchall()
    return templates.TemplateResponse("admin.html", {"request": request, "users": users})

# --- Страница добавления пользователя ---
@app.get("/admin/add_user_form", response_class=HTMLResponse)
async def add_user_form(request: Request):
    return templates.TemplateResponse("add_user.html", {"request": request})

# --- Обработка добавления пользователя ---
@app.post("/admin/add_user")
async def add_user(
    login: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(""),
    phone: str = Form(""),
    role: str = Form(""),
    iin: str = Form("")
):
    producer: DBProducer = app.state.db_producer
    exists = await producer.check_free(login=login)
    if exists["login"]:
        return RedirectResponse("/admin", status_code=303)
    await producer.add_user(login, password, full_name, phone, role, iin)
    return RedirectResponse("/admin", status_code=303)

# --- Удаление пользователя (мягкое удаление) ---
@app.get("/admin/delete/{login}")
async def delete_user(login: str):
    producer: DBProducer = app.state.db_producer
    await producer.del_user(login)
    return RedirectResponse("/admin", status_code=303)

# --- Восстановление пользователя ---
@app.get("/admin/restore/{login}")
async def restore_user(login: str):
    producer: DBProducer = app.state.db_producer
    await producer.restore_user(login)
    return RedirectResponse("/admin", status_code=303)

# --- Разблокировка пользователя ---
@app.get("/admin/unblock/{login}")
async def admin_unblock_user(login: str):
    producer: DBProducer = app.state.db_producer
    await producer.unblock(login)
    return RedirectResponse("/admin", status_code=303)

# --- Создание резервной копии БД ---
@app.get("/admin/backup")
async def admin_backup():
    producer: DBProducer = app.state.db_producer
    await producer.backup("manual_backup")
    return RedirectResponse("/admin", status_code=303)

@app.get("/admin/upload_document_form", response_class=HTMLResponse)
async def upload_document_form(request: Request):
    return templates.TemplateResponse("upload_document.html", {"request": request})

@app.post("/admin/upload_document")
async def upload_document(file: UploadFile = File(...), password: str = Form(...)):
    from modules.crypto_module import encrypt_file
    upload_dir = os.path.join(BASE_DIR, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Шифруем файл
    encrypt_file(file_path, password)
    os.remove(file_path)  # Удаляем открытый файл после шифрования

    return RedirectResponse("/admin", status_code=303)

# --- Запуск сервера ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
