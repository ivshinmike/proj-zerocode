
# 🧠 password_manager.py

import os
import sqlite3
import hashlib
import secrets
import string
import getpass
from cryptography.fernet import Fernet


DB_FILE = "passwords.db"
KEY_FILE = ".key"


# ==========================================================
# DatabaseManager
# ==========================================================
class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.row_factory = sqlite3.Row
        self.init_database()

    def init_database(self):
        cur = self.conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS master (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            login TEXT NOT NULL,
            password_encrypted BLOB NOT NULL
        )
        """)

        self.conn.commit()

    # ---- master password ----
    def set_master_password(self, password: str):
        salt = secrets.token_hex(16)
        hashed = self._hash_password(password, salt)

        self.conn.execute("""
        INSERT OR REPLACE INTO master (id, password_hash, salt)
        VALUES (1, ?, ?)
        """, (hashed, salt))
        self.conn.commit()

    def get_master_password(self):
        row = self.conn.execute(
            "SELECT password_hash, salt FROM master WHERE id = 1"
        ).fetchone()
        return row

    def verify_master_password(self, password: str) -> bool:
        row = self.get_master_password()
        if not row:
            return False
        return self._hash_password(password, row["salt"]) == row["password_hash"]

    # ---- passwords ----
    def add_password(self, name, login, encrypted_password):
        self.conn.execute("""
        INSERT INTO passwords (name, login, password_encrypted)
        VALUES (?, ?, ?)
        """, (name, login, encrypted_password))
        self.conn.commit()

    def get_password(self, name):
        return self.conn.execute(
            "SELECT * FROM passwords WHERE name = ?", (name,)
        ).fetchone()

    def list_passwords(self):
        return self.conn.execute(
            "SELECT name, login FROM passwords ORDER BY name"
        ).fetchall()

    def delete_password(self, name):
        self.conn.execute(
            "DELETE FROM passwords WHERE name = ?", (name,)
        )
        self.conn.commit()

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        return hashlib.sha256((password + salt).encode()).hexdigest()


# ==========================================================
# EncryptionManager
# ==========================================================
class EncryptionManager:
    def __init__(self):
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "rb") as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(KEY_FILE, "wb") as f:
                f.write(self.key)

        self.fernet = Fernet(self.key)

    def encrypt(self, data: str) -> bytes:
        return self.fernet.encrypt(data.encode())

    def decrypt(self, token: bytes) -> str:
        return self.fernet.decrypt(token).decode()


# ==========================================================
# PasswordGenerator / CLI
# ==========================================================
class PasswordGenerator:
    def __init__(self):
        self.db = DatabaseManager()
        self.crypto = EncryptionManager()
        self.setup_master_password()
        self.authenticate()

    # ---- auth ----
    def setup_master_password(self):
        if self.db.get_master_password():
            return

        print("🔐 Первый запуск. Создайте мастер-пароль.")
        while True:
            p1 = getpass.getpass("Мастер-пароль: ")
            p2 = getpass.getpass("Повторите: ")
            if p1 and p1 == p2:
                self.db.set_master_password(p1)
                print("✅ Мастер-пароль сохранён.")
                return
            print("❌ Пароли не совпали.")

    def authenticate(self):
        for _ in range(3):
            pwd = getpass.getpass("Введите мастер-пароль: ")
            if self.db.verify_master_password(pwd):
                return
            print("❌ Неверный пароль.")
        raise SystemExit("Слишком много попыток.")

    # ---- operations ----
    def add_password(self):
        name = input("Название: ")
        login = input("Логин: ")
        password = getpass.getpass("Пароль: ")

        encrypted = self.crypto.encrypt(password)
        self.db.add_password(name, login, encrypted)
        print("✅ Пароль сохранён.")

    def generate_password_interactive(self):
        length = int(input("Длина (по умолчанию 16): ") or 16)

        chars = (
            string.ascii_lowercase +
            string.ascii_uppercase +
            string.digits +
            "!@#$%^&*()"
        )

        password = "".join(secrets.choice(chars) for _ in range(length))
        print("🔑 Новый пароль:", password)

    def get_password(self):
        name = input("Название: ")
        row = self.db.get_password(name)
        if not row:
            print("❌ Не найдено.")
            return
        password = self.crypto.decrypt(row["password_encrypted"])
        print(f"Логин: {row['login']}")
        print(f"Пароль: {password}")

    def list_passwords(self):
        rows = self.db.list_passwords()
        if not rows:
            print("Пока пусто.")
            return
        for r in rows:
            print(f"- {r['name']} ({r['login']})")

    def delete_password(self):
        name = input("Название: ")
        self.db.delete_password(name)
        print("🗑 Удалено.")

    # ---- menu ----
    def show_menu(self):
        while True:
            print("""
1. Добавить пароль
2. Получить пароль
3. Список паролей
4. Удалить пароль
5. Сгенерировать пароль
0. Выход
""")
            choice = input("> ")

            if choice == "1":
                self.add_password()
            elif choice == "2":
                self.get_password()
            elif choice == "3":
                self.list_passwords()
            elif choice == "4":
                self.delete_password()
            elif choice == "5":
                self.generate_password_interactive()
            elif choice == "0":
                break
            else:
                print("Неверный выбор.")


# ==========================================================
if __name__ == "__main__":
    PasswordGenerator().show_menu()
