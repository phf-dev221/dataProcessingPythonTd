from flask import Flask
from flask_cors import CORS
from config import Config
from database import db, migrate
from flask_jwt_extended import JWTManager

from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

from models.user import User
from models.history import History

from routes.auth import auth_bp
from routes.files import files_bp
from routes.history import history_bp
from routes.stats import stats_bp

app = Flask(__name__)
app.config.from_object(Config)

# Initialise db et migrate
db.init_app(app)
migrate.init_app(app, db)

jwt = JWTManager(app)

from flask_cors import CORS

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "http://localhost:5173",
                "https://dataprocessingpythontd.onrender.com",
                "https://datablist.terangacode.com"
            ]
        }
    },
    supports_credentials=True
)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

# Blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(files_bp, url_prefix='/files')
app.register_blueprint(stats_bp, url_prefix='/stats')
app.register_blueprint(history_bp, url_prefix='/history')


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
