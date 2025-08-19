import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import psycopg2
from datetime import datetime
from urllib.parse import urlparse
import validators
import requests
from bs4 import BeautifulSoup

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

def get_db_connection():
    """Подключение к базе данных"""
    try:
        if os.getenv('DATABASE_URL'):
            return psycopg2.connect(os.getenv('DATABASE_URL'))
       
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def init_database():
    """Инициализация базы данных - создание таблиц если их нет"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Создаем таблицу urls если не существует
        cur.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                name VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Создаем таблицу url_checks если не существует
        cur.execute("""
            CREATE TABLE IF NOT EXISTS url_checks (
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
        print("Database tables created or already exist")
        
    except Exception as e:
        print(f"Database initialization warning: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

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

def analyze_url(url):
    """Анализ URL и извлечение информации"""
    try:
        # Выполняем запрос с таймаутом
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Проверяем статус код
        
        # Парсим HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Извлекаем заголовок
        title_tag = soup.find('title')
        title = title_tag.text.strip() if title_tag else ''
        
        # Извлекаем h1
        h1_tag = soup.find('h1')
        h1 = h1_tag.text.strip() if h1_tag else ''
        
        # Извлекаем meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc['content'].strip() if meta_desc and meta_desc.get('content') else ''
        
        return {
            'status_code': response.status_code,
            'title': title[:255],
            'h1': h1[:255],
            'description': description
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Analysis error: {e}")
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
        
        # Проверяем существование таблицы url_checks
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'url_checks'
            )
        """)
        checks_table_exists = cur.fetchone()[0]
        
        if checks_table_exists:
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
        else:
            # Если таблицы проверок нет, показываем только URLs
            cur.execute("""
                SELECT 
                    id, 
                    name, 
                    NULL as last_check_date,
                    NULL as status_code
                FROM urls 
                ORDER BY id DESC
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
        
        # Проверяем существование таблицы url_checks
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'url_checks'
            )
        """)
        checks_table_exists = cur.fetchone()[0]
        
        checks = []
        if checks_table_exists:
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
        
        # Получаем URL для проверки
        cur.execute("SELECT name FROM urls WHERE id = %s", (id,))
        url_result = cur.fetchone()
        
        if not url_result:
            flash('Страница не найдена', 'danger')
            return redirect(url_for('index'))
        
        url = url_result[0]
        
        # Анализируем URL
        analysis_result = analyze_url(url)
        
        if not analysis_result:
            flash('Произошла ошибка при проверке', 'danger')
            return redirect(url_for('url_detail', id=id))
        
        # Сохраняем результаты проверки
        cur.execute(
            """INSERT INTO url_checks 
               (url_id, status_code, h1, title, description, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (id, analysis_result['status_code'], analysis_result['h1'], 
             analysis_result['title'], analysis_result['description'], datetime.now())
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Страница успешно проверена', 'success')
        return redirect(url_for('url_detail', id=id))
        
    except Exception as e:
        flash(f'Произошла ошибка при проверке страницы: {e}', 'danger')
        return redirect(url_for('url_detail', id=id))