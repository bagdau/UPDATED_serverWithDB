import hashlib
import hmac
import base64
import time
from modules.logger import Logger
from modules.database import DocumentDatabase

log = Logger()

class AuthManager:
    def __init__(self, secret_key: str, db_path: str):
        self.secret_key = secret_key.encode()
        self.db = DocumentDatabase(db_path)

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return self.hash_password(password) == hashed_password

    # ---------- Генерация токенов ----------
    def generate_token(self, username: str, expire_in_seconds: int) -> str:
        expiration = int(time.time()) + expire_in_seconds
        data = f"{username}:{expiration}"
        signature = hmac.new(self.secret_key, data.encode(), hashlib.sha256).digest()
        token = f"{data}:{base64.urlsafe_b64encode(signature).decode()}"
        return base64.urlsafe_b64encode(token.encode()).decode()

    def generate_access_token(self, username: str) -> str:
        return self.generate_token(username, expire_in_seconds=3600)  # 1 час

    def generate_refresh_token(self, username: str) -> str:
        return self.generate_token(username, expire_in_seconds=2592000)  # 30 дней

    # ---------- Проверка токена ----------
    def verify_token(self, token: str) -> bool:
        try:
            decoded = base64.urlsafe_b64decode(token.encode()).decode()
            username, expiration, signature_b64 = decoded.split(":")
            if int(expiration) < int(time.time()):
                log.warning("Токен истёк.")
                return False

            data = f"{username}:{expiration}"
            expected_signature = hmac.new(self.secret_key, data.encode(), hashlib.sha256).digest()
            valid = hmac.compare_digest(base64.urlsafe_b64encode(expected_signature).decode(), signature_b64)
            
            if not valid:
                log.warning("Неверная подпись токена.")
            return valid
        except Exception as e:
            log.error(f"Ошибка проверки токена: {e}")
            return False

    # ---------- Освежение Access Token ----------
    def refresh_access_token(self, refresh_token: str) -> str | None:
        if self.verify_token(refresh_token):
            decoded = base64.urlsafe_b64decode(refresh_token.encode()).decode()
            username = decoded.split(":")[0]
            log.info(f"Обновление Access Token для пользователя: {username}")
            return self.generate_access_token(username)
        log.warning("Невалидный Refresh Token.")
        return None

    # ---------- Роли ----------
    def has_role(self, username: str, required_role: str) -> bool:
        roles = self.db.get_user_roles(username)
        return required_role in roles
