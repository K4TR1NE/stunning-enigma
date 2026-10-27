import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = "users.db"
LOCK_DAYS = 30
MAX_ATTEMPTS = 3

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            is_blocked INTEGER NOT NULL DEFAULT 0,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            must_change_password INTEGER NOT NULL DEFAULT 0,
            last_login TEXT
        )
    """)
    connection.commit()

    cursor.execute("SELECT id FROM users WHERE login = ?", ("admin",))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (login, password_hash, role, must_change_password) "
            "VALUES (?, ?, ?, ?)",
            ("admin", generate_password_hash("admin"), "admin", 1)
        )
        connection.commit()
    connection.close()

def find_user(login):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE login = ?", (login,))
    user = cursor.fetchone()
    connection.close()
    return user

def find_user_by_id(user_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    connection.close()
    return user

def all_users():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users ORDER BY id")
    users = cursor.fetchall()
    connection.close()
    return users

def create_user(login, password, role="user", must_change=0):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (login, password_hash, role, must_change_password) "
            "VALUES (?, ?, ?, ?)",
            (login, generate_password_hash(password), role, must_change)
        )
        connection.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        connection.close()

def update_user(user_id, **fields):
    if not fields:
        return
    columns = []
    values = []
    for column, value in fields.items():
        columns.append(f"{column} = ?")
        values.append(value)
    values.append(user_id)

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"UPDATE users SET {', '.join(columns)} WHERE id = ?", values)
    connection.commit()
    connection.close()

def set_password(user_id, new_password):
    update_user(
        user_id,
        password_hash=generate_password_hash(new_password),
        must_change_password=0,
    )

def register_failed_attempt(user):
    """Увеличивает счётчик ошибок. На 3-й раз блокирует."""
    attempts = user["failed_attempts"] + 1
    blocked = 1 if attempts >= MAX_ATTEMPTS else user["is_blocked"]
    update_user(user["id"], failed_attempts=attempts, is_blocked=blocked)
    return blocked

def reset_attempts(user_id):
    update_user(user_id, failed_attempts=0)

def mark_login(user_id):
    update_user(user_id, last_login=datetime.now().isoformat(timespec="seconds"))

def auto_block_inactive():
    threshold = (datetime.now() - timedelta(days=LOCK_DAYS)).isoformat(timespec="seconds")
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE users SET is_blocked = 1 "
        "WHERE last_login IS NOT NULL AND last_login < ? AND is_blocked = 0",
        (threshold,)
    )
    connection.commit()
    connection.close()

def check_password(user, password):
    return check_password_hash(user["password_hash"], password)