from urllib.parse import urlparse

import validators


def normalize_url(url):
    """Нормализация URL"""
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def validate_url(url):
    """Валидация URL"""
    if not url:
        return "URL обязателен для заполнения"
    if len(url) > 255:
        return "URL не должен превышать 255 символов"
    if not validators.url(url):
        return "Некорректный URL"
    return None
