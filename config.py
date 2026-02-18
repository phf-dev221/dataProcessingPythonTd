import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('API_SECRET_KEY', 'supersecretkey')

    # Récupère l'URL PostgreSQL si dispo, sinon SQLite en local
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database.db')

    # Render donne parfois postgres:// au lieu de postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    # Engine options adaptées : pas de check_same_thread pour PostgreSQL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"connect_timeout": 10} if DATABASE_URL.startswith('postgresql') else {"timeout": 60, "check_same_thread": False}
    }

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'une-cle-beaucoup-plus-longue-32-chars-minimum')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)