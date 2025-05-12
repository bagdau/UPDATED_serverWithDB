import logging
from logging.handlers import RotatingFileHandler
import os

class Logger:
    def __init__(self, log_dir="logs", log_file="server.log", max_size=1_000_000, backup_count=5):
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, log_file)

        self.logger = logging.getLogger("SecureServerLogger")
        self.logger.setLevel(logging.DEBUG)

        # Формат логов
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s]: %(message)s", "%Y-%m-%d %H:%M:%S")

        # Хэндлер для файла с ротацией
        file_handler = RotatingFileHandler(log_path, maxBytes=max_size, backupCount=backup_count)
        file_handler.setFormatter(formatter)

        # Хэндлер для консоли
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Добавляем хэндлеры
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def debug(self, message: str):
        self.logger.debug(message)
