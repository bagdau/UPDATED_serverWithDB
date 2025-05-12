import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла (если он есть)
load_dotenv()

class Config:
    # --- Базовые настройки ---
    DEBUG = os.getenv("DEBUG", "True") == "True"
    SECRET_KEY = os.getenv("SECRET_KEY", "SuperSecretKey123")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "secure_storage.db")

    # --- Настройки Email ---
    EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "True") == "True"
    EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.example.com")
    EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", 587))
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "your_email@example.com")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your_email_password")
    EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "admin@example.com")

    # --- Настройки Telegram ---
    TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "True") == "True"
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")

    # --- Настройки прокси ---
    PROXIES = os.getenv("PROXIES", "").split(",")  # Через запятую в .env

    # --- Настройки SSL ---
    VERIFY_SSL = os.getenv("VERIFY_SSL", "True") == "True"
    CERT_PATH = os.getenv("CERT_PATH", "")

    @staticmethod
    def print_config():
        print(f"DEBUG: {Config.DEBUG}")
        print(f"DATABASE_PATH: {Config.DATABASE_PATH}")
        print(f"EMAIL_ENABLED: {Config.EMAIL_ENABLED}")
        print(f"TELEGRAM_ENABLED: {Config.TELEGRAM_ENABLED}")
        print(f"PROXIES: {Config.PROXIES}")
