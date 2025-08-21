from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from datetime import datetime

from .database import (
    init_database,
    add_url_to_db,
    get_url_by_name,
    get_all_urls,
    get_url_by_id,
    get_checks_by_url_id,
    add_url_check,
)
from .parser import analyze_url
from .url import normalize_url, validate_url

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"  # Должно быть в .env

# Инициализируем базу данных при запуске
init_database()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/urls", methods=["POST"])
def add_url():
    url = request.form.get("url", "").strip()

    error = validate_url(url)
    if error:
        flash(error, "danger")
        return render_template("index.html", url=url), 422

    normalized_url = normalize_url(url)

    try:
        # Проверяем существование URL
        existing_url_id = get_url_by_name(normalized_url)

        if existing_url_id:
            flash("Страница уже существует", "info")
            url_id = existing_url_id
        else:
            # Добавляем новый URL
            url_id = add_url_to_db(normalized_url, datetime.now())
            flash("Страница успешно добавлена", "success")

        return redirect(url_for("url_detail", id=url_id))

    except Exception as e:
        flash(f"Произошла ошибка при добавлении страницы: {e}", "danger")
        return render_template("index.html", url=url), 500


@app.route("/urls")
def urls_list():
    try:
        urls = get_all_urls()
        return render_template("urls.html", urls=urls)
    except Exception as e:
        flash(f"Произошла ошибка при загрузке списка сайтов: {e}", "danger")
        return redirect(url_for("index"))


@app.route("/urls/<int:id>")
def url_detail(id):
    try:
        url = get_url_by_id(id)
        if not url:
            flash("Страница не найдена", "danger")
            return redirect(url_for("index"))

        checks = get_checks_by_url_id(id)
        return render_template("url_detail.html", url=url, checks=checks)

    except Exception as e:
        flash(f"Произошла ошибка при загрузке страницы: {e}", "danger")
        return redirect(url_for("index"))


@app.route("/urls/<int:id>/checks", methods=["POST"])
def check_url(id):
    try:
        url = get_url_by_id(id)
        if not url:
            flash("Страница не найдена", "danger")
            return redirect(url_for("index"))

        # Анализируем URL
        analysis_result = analyze_url(url[1])

        if not analysis_result:
            flash("Произошла ошибка при проверке", "danger")
            return redirect(url_for("url_detail", id=id))

        # Сохраняем результаты проверки
        add_url_check(
            {
                "url_id": id,
                "status_code": analysis_result["status_code"],
                "h1": analysis_result["h1"],
                "title": analysis_result["title"],
                "description": analysis_result["description"],
                "created_at": datetime.now(),
            }
        )

        flash("Страница успешно проверена", "success")
        return redirect(url_for("url_detail", id=id))

    except Exception as e:
        flash(f"Произошла ошибка при проверке страницы: {e}", "danger")
        return redirect(url_for("url_detail", id=id))
