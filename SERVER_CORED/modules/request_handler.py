from flask import request, jsonify
from functools import wraps
from modules.auth import AuthManager
from modules.logger import Logger

log = Logger()

class RequestHandler:
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager

    def get_json(self):
        try:
            data = request.get_json(force=True)
            log.debug(f"Получены JSON данные: {data}")
            return data
        except Exception as e:
            log.warning(f"Ошибка парсинга JSON: {e}")
            return {}

    def get_args(self):
        args = request.args.to_dict()
        log.debug(f"Получены GET параметры: {args}")
        return args

    def get_headers(self):
        headers = dict(request.headers)
        log.debug(f"Получены заголовки: {headers}")
        return headers

    def get_token(self):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            log.debug(f"Извлечён токен: {token}")
            return token
        log.warning("Токен не найден в заголовках.")
        return None

    def is_authenticated(self):
        token = self.get_token()
        if token and self.auth_manager.verify_token(token):
            log.info("Токен подтверждён. Пользователь аутентифицирован.")
            return True
        log.warning("Аутентификация не удалась.")
        return False

    def has_access(self, required_role: str):
        token = self.get_token()
        if not token:
            return False
        try:
            decoded = self.auth_manager._decode_token(token)
            username = decoded.split(":")[0]
            return self.auth_manager.has_role(username, required_role)
        except Exception as e:
            log.warning(f"Ошибка проверки роли: {e}")
            return False

    # Декоратор для проверки токена и роли
    def require_auth(self, required_role: str = None):
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                token = self.get_token()
                if not token or not self.auth_manager.verify_token(token):
                    return jsonify({"error": "Unauthorized"}), 401

                if required_role:
                    decoded = self.auth_manager._decode_token(token)
                    username = decoded.split(":")[0]
                    if not self.auth_manager.has_role(username, required_role):
                        return jsonify({"error": "Forbidden"}), 403

                return f(*args, **kwargs)
            return wrapper
        return decorator
