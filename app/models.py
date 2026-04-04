from datetime import datetime
from . import db


class User(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)  # ← CHANGE to nullable=True
    email = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default="user")
    verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6), nullable=True)
    code_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    
    # NEW COLUMNS for OAuth
    auth_provider = db.Column(db.String(20), default='email')  # 'email' or 'google'
    google_id = db.Column(db.String(100), nullable=True, unique=True)  # Google's unique ID