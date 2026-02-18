import os
from datetime import timedelta

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('API_SECRET_KEY', 'supersecretkey')

    # Flask-SQLAlchemy utilise cette variable précise
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"timeout": 60, "check_same_thread": False}
    }

    JWT_SECRET_KEY = "une-cle-beaucoup-plus-longue-32-chars-minimum"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)