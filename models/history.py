from database import db
from datetime import datetime

class History(db.Model):
    __tablename__ = "history"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename   = db.Column(db.String(255), nullable=False)
    action     = db.Column(db.String(50), nullable=False)  # 'clean' ou 'convert'
    rows       = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship("User", backref="history")