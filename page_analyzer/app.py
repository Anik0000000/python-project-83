import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import psycopg2
from datetime import datetime
from urllib.parse import urlparse
import validators

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

def get_db_connection():
    """Подключение к базе данных с приоритетом на DATABASE_URL от Render"""
    try:
        if os.getenv('DATABASE_URL'):
            return psycopg2.connect(os.getenv('DATABASE_URL'))
       
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def init_database():
    """Инициализация базы данных - создание таблиц если их нет"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверяем существование таблицы urls
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'urls'
            )
        """)
        urls_exists = cur.fetchone()[0]
        
        if not urls_exists:
            print("Creating urls table...")
            cur.execute("""
                CREATE TABLE urls (
                    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        # Проверяем существование таблицы url_checks
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'url_checks'
            )
        """)
        checks_exists = cur.fetchone()[0]
        
        if not checks_exists:
            print("Creating url_checks table...")
            cur.execute("""
                CREATE TABLE url_checks (
                    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                    url_id BIGINT REFERENCES urls(id) ON DELETE CASCADE,
                    status_code INTEGER,
                    h1 VARCHAR(255),
                    title VARCHAR(255),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully")
        
    except Exception as e:
        print(f"Database initialization error: {e}")

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

# Инициализируем базу данных при запуске
init_database()

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
        
        cur.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
        existing_url = cur.fetchone()
        
        if existing_url:
            url_id = existing_url[0]
            flash('Страница уже существует', 'info')
        else:
            cur.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
                (normalized_url, datetime.now())
            )
            url_id = cur.fetchone()[0]
            flash('Страница успешно добавлена', 'success')
        
        conn.commit()
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
        
        cur.execute("""
            SELECT 
                u.id, 
                u.name, 
                uc.created_at as last_check_date,
                uc.status_code
            FROM urls u
            LEFT JOIN url_checks uc ON u.id = uc.url_id 
            AND uc.id = (
                SELECT MAX(id) FROM url_checks WHERE url_id = u.id
            )
            ORDER BY u.id DESC
        """)
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
        
        # Получаем информацию о URL
        cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (id,))
        url = cur.fetchone()
        
        if not url:
            flash('Страница не найдена', 'danger')
            return redirect(url_for('index'))
        
        # Получаем проверки для этого URL
        cur.execute("""
            SELECT id, status_code, h1, title, description, created_at 
            FROM url_checks 
            WHERE url_id = %s 
            ORDER BY id DESC
        """, (id,))
        checks = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('url_detail.html', url=url, checks=checks)
        
    except Exception as e:
        flash(f'Произошла ошибка при загрузке страницы: {e}', 'danger')
        return redirect(url_for('index'))

@app.route('/urls/<int:id>/checks', methods=['POST'])
def check_url(id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверяем существование URL
        cur.execute("SELECT id FROM urls WHERE id = %s", (id,))
        if not cur.fetchone():
            flash('Страница не найдена', 'danger')
            return redirect(url_for('index'))
        
        # Создаем новую проверку (пока только базовые поля)
        cur.execute(
            "INSERT INTO url_checks (url_id, created_at) VALUES (%s, %s)",
            (id, datetime.now())
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Страница успешно проверена', 'success')
        return redirect(url_for('url_detail', id=id))
        
    except Exception as e:
        flash(f'Произошла ошибка при проверке страницы: {e}', 'danger')
        return redirect(url_for('url_detail', id=id))