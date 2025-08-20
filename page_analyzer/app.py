import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import psycopg
from psycopg import sql
from datetime import datetime
from urllib.parse import urlparse
import validators
import requests
from bs4 import BeautifulSoup
import re

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

def get_db_connection():
    """Подключение к базе данных с использованием psycopg3"""
    try:
        if os.getenv('DATABASE_URL'):
            return psycopg.connect(os.getenv('DATABASE_URL'))
      
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

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
    """Анализ URL и извлечение SEO-информации"""
    try:
        # Выполняем запрос с таймаутом и user-agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Проверяем статус код
        
        # Парсим HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Извлекаем заголовок (title)
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ''
        
        # Извлекаем h1 (берем только первый, если несколько)
        h1_tag = soup.find('h1')
        h1 = h1_tag.get_text().strip() if h1_tag else ''
        
        # Извлекаем meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = ''
        if meta_desc and meta_desc.get('content'):
            description = meta_desc['content'].strip()
        
        # Альтернативные способы поиска description
        if not description:
            meta_desc = soup.find('meta', attrs={'property': 'og:description'})
            if meta_desc and meta_desc.get('content'):
                description = meta_desc['content'].strip()
        
        # Ограничиваем длину для базы данных
        return {
            'status_code': response.status_code,
            'title': title[:255] if title else '',
            'h1': h1[:255] if h1 else '',
            'description': description
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Analysis error: {e}")
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
        
        # Проверяем существование URL
        result = conn.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
        existing_url = result.fetchone()
        
        if existing_url:
            url_id = existing_url[0]
            flash('Страница уже существует', 'info')
        else:
            # Добавляем новый URL
            result = conn.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
                (normalized_url, datetime.now())
            )
            url_id = result.fetchone()[0]
            flash('Страница успешно добавлена', 'success')
        
        conn.commit()
        conn.close()
        return redirect(url_for('url_detail', id=url_id))
        
    except Exception as e:
        flash(f'Произошла ошибка при добавлении страницы: {e}', 'danger')
        return render_template('index.html', url=url), 500

@app.route('/urls')
def urls_list():
    try:
        conn = get_db_connection()
        
        result = conn.execute("""
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
        
        urls = result.fetchall()
        conn.close()
        return render_template('urls.html', urls=urls)
        
    except Exception as e:
        flash(f'Произошла ошибка при загрузке списка сайтов: {e}', 'danger')
        return redirect(url_for('index'))

@app.route('/urls/<int:id>')
def url_detail(id):
    try:
        conn = get_db_connection()
        
        # Получаем информацию о URL
        result = conn.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (id,))
        url = result.fetchone()
        
        if not url:
            flash('Страница не найдена', 'danger')
            return redirect(url_for('index'))
        
        # Получаем проверки для этого URL
        result = conn.execute("""
            SELECT id, status_code, h1, title, description, created_at 
            FROM url_checks 
            WHERE url_id = %s 
            ORDER BY id DESC
        """, (id,))
        
        checks = result.fetchall()
        conn.close()
        
        return render_template('url_detail.html', url=url, checks=checks)
        
    except Exception as e:
        flash(f'Произошла ошибка при загрузке страницы: {e}', 'danger')
        return redirect(url_for('index'))

@app.route('/urls/<int:id>/checks', methods=['POST'])
def check_url(id):
    try:
        conn = get_db_connection()
        
        # Получаем URL для проверки
        result = conn.execute("SELECT name FROM urls WHERE id = %s", (id,))
        url_result = result.fetchone()
        
        if not url_result:
            flash('Страница не найдена', 'danger')
            return redirect(url_for('index'))
        
        url = url_result[0]
        
        # Анализируем URL
        analysis_result = analyze_url(url)
        
        if not analysis_result:
            flash('Произошла ошибка при проверке', 'danger')
            return redirect(url_for('url_detail', id=id))
        
        # Сохраняем результаты проверки с SEO-данными
        conn.execute(
            """INSERT INTO url_checks 
               (url_id, status_code, h1, title, description, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (id, 
             analysis_result['status_code'], 
             analysis_result['h1'], 
             analysis_result['title'], 
             analysis_result['description'], 
             datetime.now())
        )
        
        conn.commit()
        conn.close()
        
        flash('Страница успешно проверена', 'success')
        return redirect(url_for('url_detail', id=id))
        
    except Exception as e:
        flash(f'Произошла ошибка при проверке страницы: {e}', 'danger')
        return redirect(url_for('url_detail', id=id))

if __name__ == '__main__':
    app.run(debug=True)