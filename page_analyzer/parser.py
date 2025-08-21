import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def analyze_url(url):
    """Анализ URL и извлечение SEO-информации"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Извлекаем заголовок
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ''
        
        # Извлекаем h1
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