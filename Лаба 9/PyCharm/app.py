from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort
)
from database import (
    init_db, find_user, create_user, all_users,
    update_user, set_password, find_user_by_id,
    check_password, register_failed_attempt
)
from auth import (
    authenticate, login_user, logout_user,
    current_user, login_required, admin_required
)
import random

app = Flask(__name__)
app.secret_key = "zooshop-secret-key"
init_db()


def generate_captcha_order():
    order = [1, 2, 3, 4]
    random.shuffle(order)
    return order


@app.route("/")
def index(): return render_template("index.html")


@app.route("/catalog")
def catalog(): return render_template("catalog.html")


@app.route("/product")
def product(): return render_template("product.html")


@app.route("/cart")
def cart(): return render_template("cart.html")


@app.route("/checkout")
@login_required
def checkout(): return render_template("checkout.html")


@app.route("/about")
def about(): return render_template("about.html")


@app.route("/contacts")
def contacts(): return render_template("contacts.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        login_value = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not login_value or not password or not confirm:
            flash("Все поля обязательны для заполнения", "error")
            return render_template("register.html")
        if password != confirm:
            flash("Пароль и подтверждение не совпадают", "error")
            return render_template("register.html")
        if find_user(login_value):
            flash("Пользователь с указанным логином уже существует", "error")
            return render_template("register.html")

        create_user(login_value, password, role="user", must_change=0)
        flash("Регистрация прошла успешно. Теперь войдите в систему", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        session['captcha_order'] = generate_captcha_order()
        return render_template("login.html", captcha_order=session['captcha_order'])

    if request.method == "POST":
        login_value = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        user_puzzle = request.form.get("puzzle_order", "")

        if not login_value or not password:
            flash("Введите логин и пароль", "error")
            return render_template("login.html", captcha_order=session['captcha_order'])

        # Проверка капчи
        correct_order = session.get('captcha_order', [])
        # Переводим строку "1,2,3,4" в список [1, 2, 3, 4]
        user_order = [int(x) for x in user_puzzle.split(',')] if user_puzzle else []

        if correct_order != user_order:
            user = find_user(login_value)
            if user and register_failed_attempt(user):
                flash("Вы заблокированы. Обратитесь к администратору", "error")
                return redirect(url_for("login"))

            flash("Капча собрана неверно. Попробуйте ещё раз", "error")
            # ВАЖНО: Отдаем тот же порядок, который был! Не генерируем новый.
            return render_template("login.html", captcha_order=session['captcha_order'])

        # Проверка пароля
        status, user = authenticate(login_value, password)

        if status == "blocked":
            flash("Вы заблокированы. Обратитесь к администратору", "error")
            return redirect(url_for("login"))

        if status == "wrong":
            flash("Вы ввели неверный логин или пароль. Пожалуйста проверьте ещё раз введенные данные", "error")
            # Тоже отдаем тот же порядок
            return render_template("login.html", captcha_order=session['captcha_order'])

        login_user(user)
        flash("Вы успешно авторизовались", "success")

        if user["must_change_password"]:
            return redirect(url_for("change_password"))
        if user["role"] == "admin":
            return redirect(url_for("admin_panel"))
        return redirect(url_for("index"))

    return redirect(url_for("login"))


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    user = current_user()
    if request.method == "POST":
        current = request.form.get("current", "")
        new = request.form.get("new", "")
        confirm = request.form.get("confirm", "")
        if not current or not new or not confirm or new != confirm or len(new) < 6:
            flash("Ошибка. Проверьте пароли (мин. 6 символов).", "error")
            return render_template("change_password.html")
        if not check_password(user, current):
            flash("Текущий пароль введён неверно", "error")
            return render_template("change_password.html")
        set_password(user["id"], new)
        flash("Пароль успешно изменён", "success")
        return redirect(url_for("admin_panel") if user["role"] == "admin" else url_for("index"))
    return render_template("change_password.html")


@app.route("/logout")
def logout():
    logout_user()
    flash("Вы вышли из системы", "info")
    return redirect(url_for("index"))


@app.route("/admin")
@login_required
@admin_required
def admin_panel():
    return render_template("admin.html", users=all_users())


@app.route("/admin/add", methods=["GET", "POST"])
@login_required
@admin_required
def admin_add():
    if request.method == "POST":
        login_value = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        if find_user(login_value):
            flash("Пользователь с указанным логином уже существует", "error")
            return render_template("admin_user_form.html", action="add")
        create_user(login_value, password, role=request.form.get("role", "user"), must_change=1)
        flash(f"Пользователь «{login_value}» добавлен", "success")
        return redirect(url_for("admin_panel"))
    return render_template("admin_user_form.html", action="add")


@app.route("/admin/edit/<int:user_id>", methods=["GET", "POST"])
@login_required
@admin_required
def admin_edit(user_id):
    user = find_user_by_id(user_id)
    if request.method == "POST":
        new_blocked = 1 if request.form.get("is_blocked") else 0
        update_user(user_id, role=request.form.get("role"), is_blocked=new_blocked)
        if new_blocked == 0: update_user(user_id, failed_attempts=0)
        flash("Данные обновлены", "success")
        return redirect(url_for("admin_panel"))
    return render_template("admin_user_form.html", action="edit", user=user)


@app.errorhandler(404)
def not_found(error): return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)