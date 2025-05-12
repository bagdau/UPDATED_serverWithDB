import sqlite3
import os
from cryptography.fernet import Fernet
from datetime import datetime
import hashlib

class DocumentDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.create_tables()

    def get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def create_tables(self):
        with self.get_connection() as conn:
            queries = [
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password_hash TEXT
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_name TEXT UNIQUE
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id INTEGER,
                    role_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (role_id) REFERENCES roles(id)
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    filepath TEXT,
                    category TEXT,
                    tags TEXT,
                    date_added TEXT,
                    encryption_key TEXT
                );
                """
            ]
            for query in queries:
                conn.execute(query)
            conn.commit()

    # ---------- Пользователи ----------
    def add_user(self, username: str, password: str):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                (username, password_hash)
            )
            conn.commit()

    def verify_user(self, username: str, password: str) -> bool:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM users WHERE username = ? AND password_hash = ?", 
                (username, password_hash)
            )
            return cursor.fetchone() is not None

    def user_exists(self, username: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM users WHERE username = ?", 
                (username,)
            )
            return cursor.fetchone() is not None

    # ---------- Работа с Документами ----------
    def add_document(self, filename, filepath, category, tags):
        key = Fernet.generate_key()
        cipher = Fernet(key)

        with open(filepath, 'rb') as f:
            encrypted_data = cipher.encrypt(f.read())

        encrypted_path = f"{filepath}.enc"
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)

        os.remove(filepath)

        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO documents (filename, filepath, category, tags, date_added, encryption_key) VALUES (?, ?, ?, ?, ?, ?)",
                (filename, encrypted_path, category, tags, datetime.now().isoformat(), key.decode())
            )
            conn.commit()

    def decrypt_document(self, document_id, output_path):
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT filepath, encryption_key FROM documents WHERE id = ?", 
                (document_id,)
            )
            row = cursor.fetchone()

            if not row:
                raise ValueError("Документ не найден")

            encrypted_path, key = row
            cipher = Fernet(key.encode())

            with open(encrypted_path, 'rb') as f:
                decrypted_data = cipher.decrypt(f.read())

            with open(output_path, 'wb') as f:
                f.write(decrypted_data)

    def search_documents(self, keyword):
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM documents WHERE filename LIKE ? OR tags LIKE ? OR category LIKE ?",
                (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%")
            )
            return cursor.fetchall()
