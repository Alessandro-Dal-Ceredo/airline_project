import os
from datetime import timedelta

class Config:
    """Configurazione base dell'applicazione"""
    
    # Chiave segreta per Flask (CAMBIA IN PRODUZIONE!)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configurazione Database PostgreSQL
    POSTGRES_USER = os.environ.get('POSTGRES_USER') or 'postgres'
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD') or 'admin123'
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST') or 'localhost'
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT') or '5432'
    POSTGRES_DB = os.environ.get('POSTGRES_DB') or 'flight_booking'
    
    # URI del database
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    
    # Disabilita il tracking delle modifiche (migliora performance)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mostra le query SQL nel log (utile per debug)
    SQLALCHEMY_ECHO = os.environ.get('FLASK_ENV') == 'development'
    
    # Configurazione Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    
    # Configurazione per sessioni
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)


class DevelopmentConfig(Config):
    """Configurazione per sviluppo"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Configurazione per produzione"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    def __init__(self):
        super().__init__()
        # In produzione usa variabili d'ambiente per la sicurezza
        secret_key = os.environ.get('SECRET_KEY')
        if not secret_key:
            raise ValueError("SECRET_KEY deve essere impostato in produzione")
        self.SECRET_KEY = secret_key


class TestConfig(Config):
    """Configurazione per test"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # DB in memoria per i test
    WTF_CSRF_ENABLED = False


# Dizionario delle configurazioni
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestConfig,
    'default': DevelopmentConfig
}