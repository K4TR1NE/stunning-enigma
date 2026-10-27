from functools import wraps
from flask import session, redirect, url_for, flash
from database import (
    find_user, find_user_by_id, check_password,
    register_failed_attempt, reset_attempts, mark_login,
    auto_block_inactive
)

def authenticate(login, password):
    """Возвращает статус: ok / blocked / wrong."""
    auto_block_inactive()

    user = find_user(login)
    if not user:
        return "wrong", None

    if user["is_blocked"]:
        return "blocked", None

    if not check_password(user, password):
        register_failed_attempt(user) # Тратим попытку при неверном пароле
        return "wrong", None

    reset_attempts(user["id"]) # Сбрасываем попытки при успехе
    mark_login(user["id"])
    return "ok", user

def login_user(user):
    session["user_id"] = user["id"]
    session["login"] = user["login"]
    session["role"] = user["role"]

def logout_user():
    session.clear()

def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return find_user_by_id(user_id)

def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Сначала войдите в систему", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper

def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Доступ только для администратора", "error")
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapper