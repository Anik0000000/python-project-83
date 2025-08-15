from flask import Flask, render_template, request, redirect, url_for, flash
import os
from psycopg2 import connect, Error
from urllib.parse import urlparse
from validators import url as validate_url
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

def get_db_connection():
    return connect(os.getenv("DATABASE_URL"))

def normalize_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def is_valid_url(url):
    return (
        len(url) <= 255
        and validate_url(url)
        and urlparse(url).scheme in ("http", "https")
    )

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/urls", methods=["POST"])
def add_url():
    raw_url = request.form.get("url")
    if not is_valid_url(raw_url):
        flash("Некорректный URL", "danger")
        return render_template("index.html"), 422

    normalized_url = normalize_url(raw_url)

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
        existing_url = cur.fetchone()

        if existing_url:
            flash("Страница уже существует", "info")
            url_id = existing_url[0]
        else:
            cur.execute(
                "INSERT INTO urls (name) VALUES (%s) RETURNING id",
                (normalized_url,),
            )
            url_id = cur.fetchone()[0]
            conn.commit()
            flash("Страница успешно добавлена", "success")

        return redirect(url_for("show_url", id=url_id))

    except Error as e:
        flash(f"Ошибка базы данных: {e}", "danger")
        return render_template("index.html"), 500

    finally:
        if conn:
            conn.close()

@app.route("/urls")
def list_urls():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM urls ORDER BY created_at DESC")
    urls = cur.fetchall()
    conn.close()
    return render_template("urls/list.html", urls=urls)

@app.route("/urls/<int:id>")
def show_url(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
    url = cur.fetchone()
    conn.close()

    if not url:
        flash("Страница не найдена", "danger")
        return redirect(url_for("home"))

    return render_template("urls/show.html", url=url)