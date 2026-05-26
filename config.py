import os
import secrets
from dotenv import load_dotenv

load_dotenv()
load_dotenv('.env.production', override=True)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-only-insecure-key-change-in-production'
    basedir = os.path.abspath(os.path.dirname(__file__))

    _db_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'mediplatform.db'))
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Babel configuration for i18n
    LANGUAGES = {
        'ru': 'Русский',
        'kz': 'Қазақша',
        'en': 'English'
    }
    BABEL_DEFAULT_LOCALE = 'ru'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
