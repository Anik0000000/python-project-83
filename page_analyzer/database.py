import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Подключение к базе данных"""
    try:
        if os.getenv('DATABASE_URL'):
            return psycopg2.connect(os.getenv('DATABASE_URL'))
       
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def init_database():
    """Инициализация базы данных"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Создаем таблицы если не существуют
        with open('database.sql', 'r') as f:
            sql_commands = f.read()
        
        cur.execute(sql_commands)
        conn.commit()
        print("Database initialized successfully")
        
    except Exception as e:
        print(f"Database initialization warning: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

def add_url_to_db(url, created_at):
    """Добавление URL в базу данных"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
            (url, created_at)
        )
        url_id = cur.fetchone()[0]
        conn.commit()
        return url_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_url_by_name(url):
    """Получение URL по имени"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id FROM urls WHERE name = %s", (url,))
        result = cur.fetchone()
        return result[0] if result else None
    finally:
        cur.close()
        conn.close()

def get_all_urls():
    """Получение всех URL с последней проверкой"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
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
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def get_url_by_id(url_id):
    """Получение URL по ID"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (url_id,))
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()

def get_checks_by_url_id(url_id):
    """Получение проверок по ID URL"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT id, status_code, h1, title, description, created_at 
            FROM url_checks 
            WHERE url_id = %s 
            ORDER BY id DESC
        """, (url_id,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def add_url_check(check_data):
    """Добавление проверки URL"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO url_checks 
            (url_id, status_code, h1, title, description, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            check_data['url_id'],
            check_data['status_code'],
            check_data['h1'],
            check_data['title'],
            check_data['description'],
            check_data['created_at']
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()