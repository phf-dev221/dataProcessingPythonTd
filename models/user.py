from datetime import datetime

from pygments.lexer import default

from database import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, nullable=False)
    joinedDate = db.Column(db.DateTime, default=datetime.now(), index=True, nullable=False)
    totalFilesProcessed = db.Column(db.Integer, nullable=True, default=0)
    totalRowsCleaned = db.Column(db.Integer, nullable=True, default=0)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

