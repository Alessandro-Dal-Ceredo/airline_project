import os
from datetime import timedelta

class Config:
    """Configurazione base dell'applicazione"""

    # Chiave segreta per Flask (CAMBIA IN PRODUZIONE!)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configurazione Database PostgreSQL
    POSTGRES_USER = os.environ.get('POSTGRES_USER') or 'dalce'
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD') or ''
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST') or 'localhost'
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT') or '5432'
    POSTGRES_DB = os.environ.get('POSTGRES_DB') or 'flight_booking'

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # Mostra le query SQL nel log (utile per debug)
    SQLALCHEMY_ECHO = os.environ.get('FLASK_ENV') == 'development'

    REMEMBER_COOKIE_DURATION = timedelta(days=7)

    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True


config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig
}