from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="viewer")


class Rover(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    api_token = db.Column(db.String(128), nullable=False)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    mode_desired = db.Column(db.String(16), nullable=False, default="MANUAL")
    mode_reported = db.Column(db.String(16), nullable=False, default="MANUAL")
    pdd_state = db.Column(db.String(32), nullable=False, default="BOOT")
    last_seen = db.Column(db.DateTime, nullable=True)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rover_id = db.Column(db.String(64), db.ForeignKey("rover.id"), nullable=False)
    actor = db.Column(db.String(64), nullable=False)
    kind = db.Column(db.String(32), nullable=False)
    payload = db.Column(db.Text, nullable=False)
    ts = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
