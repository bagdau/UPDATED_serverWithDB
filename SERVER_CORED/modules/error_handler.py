from modules.logger import Logger
import traceback
import smtplib
from email.mime.text import MIMEText
import requests

log = Logger()

class CriticalError(Exception):
    """Критическая ошибка системы."""
    pass

class ValidationError(Exception):
    """Ошибка валидации данных."""
    pass

class ErrorHandler:
    # Конфигурация для уведомлений
    EMAIL_CONFIG = {
        "enabled": True,
        "smtp_server": "smtp.example.com",
        "smtp_port": 587,
        "username": "your_email@example.com",
        "password": "your_email_password",
        "recipient": "admin@example.com"
    }

    TELEGRAM_CONFIG = {
        "enabled": True,
        "bot_token": "YOUR_BOT_TOKEN",
        "chat_id": "YOUR_CHAT_ID"
    }

    @staticmethod
    def handle_exception(e: Exception, critical: bool = False):
        error_message = f"[ERROR]: {str(e)}\n{traceback.format_exc()}"
        if critical:
            log.error(f"Критическая ошибка:\n{error_message}")
            ErrorHandler.send_alert(error_message)
            raise CriticalError("Критическая ошибка. Останов системы.")
        else:
            log.warning(f"Некритичная ошибка:\n{error_message}")

    @staticmethod
    def send_alert(message: str):
        if ErrorHandler.EMAIL_CONFIG["enabled"]:
            ErrorHandler.send_email_alert(message)
        if ErrorHandler.TELEGRAM_CONFIG["enabled"]:
            ErrorHandler.send_telegram_alert(message)

    @staticmethod
    def send_email_alert(message: str):
        try:
            config = ErrorHandler.EMAIL_CONFIG
            msg = MIMEText(message)
            msg["Subject"] = "🚨 Критическая ошибка на сервере"
            msg["From"] = config["username"]
            msg["To"] = config["recipient"]

            with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
                server.starttls()
                server.login(config["username"], config["password"])
                server.send_message(msg)
            
            log.info("Уведомление на Email отправлено успешно.")
        except Exception as e:
            log.error(f"Ошибка отправки Email: {e}")

    @staticmethod
    def send_telegram_alert(message: str):
        try:
            config = ErrorHandler.TELEGRAM_CONFIG
            url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
            payload = {
                "chat_id": config["chat_id"],
                "text": f"🚨 Критическая ошибка:\n{message}",
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                log.info("Уведомление в Telegram отправлено успешно.")
            else:
                log.warning(f"Не удалось отправить уведомление в Telegram: {response.text}")
        except Exception as e:
            log.error(f"Ошибка отправки в Telegram: {e}")

    @staticmethod
    def safe_execute(func):
        """Декоратор для безопасного выполнения функций."""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ErrorHandler.handle_exception(e)
                return None
        return wrapper
