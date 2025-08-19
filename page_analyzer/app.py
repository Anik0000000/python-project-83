import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import psycopg2
from datetime import datetime
from urllib.parse import urlparse
import validators

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

def get_db_connection():
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn

def normalize_url(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"

def validate_url(url):
    if not url:
        return "URL обязателен для заполнения"
    if len(url) > 255:
        return "URL не должен превышать 255 символов"
    if not validators.url(url):
        return "Некорректный URL"
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/urls', methods=['POST'])
def add_url():
    url = request.form.get('url', '').strip()
    
    error = validate_url(url)
    if error:
        flash(error, 'danger')
        return render_template('index.html', url=url), 422
    
    normalized_url = normalize_url(url)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверяем существование URL
        cur.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
        existing_url = cur.fetchone()
        
        if existing_url:
            url_id = existing_url[0]
            flash('Страница уже существует', 'info')
        else:
            # Добавляем новый URL
            cur.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
                (normalized_url, datetime.now())
            )
            url_id = cur.fetchone()[0]
            flash('Страница успешно добавлена', 'success')
        
        cur.close()
        conn.close()
        return redirect(url_for('url_detail', id=url_id))
        
    except Exception as e:
        flash(f'Произошла ошибка при добавлении страницы: {e}', 'danger')
        return render_template('index.html', url=url), 500

@app.route('/urls')
def urls_list():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id, name, created_at FROM urls ORDER BY created_at DESC")
        urls = cur.fetchall()
        
        cur.close()
        conn.close()
        return render_template('urls.html', urls=urls)
        
    except Exception as e:
        flash(f'Произошла ошибка при загрузке списка сайтов: {e}', 'danger')
        return redirect(url_for('index'))

@app.route('/urls/<int:id>')
def url_detail(id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (id,))
        url = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not url:
            flash('Страница не найдена', 'danger')
            return redirect(url_for('index'))
        
        return render_template('url_detail.html', url=url)
        
    except Exception as e:
        flash(f'Произошла ошибка при загрузке страницы: {e}', 'danger')
        return redirect(url_for('index'))