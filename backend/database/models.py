from datetime import datetime
from . import db  # ✅ จุดสำคัญ — ใช้ “.import” (relative import)

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ocr_results = db.relationship("OcrResult", backref="user", lazy=True)


class OcrResult(db.Model):
    __tablename__ = "ocr_results"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    filename = db.Column(db.String(255))
    original_image_path = db.Column(db.String(255))
    processed_image_path = db.Column(db.String(255))
    id_number = db.Column(db.String(20))
    prefix = db.Column(db.String(20))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    dob = db.Column(db.String(50))
    address = db.Column(db.Text)
    cer = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CerResult(db.Model):
    __tablename__ = "cer_results"

    id = db.Column(db.Integer, primary_key=True)
    ocr_result_id = db.Column(db.Integer, db.ForeignKey("ocr_results.id"))
    filename = db.Column(db.String(255))
    cer_id_number = db.Column(db.Float)
    cer_prefix = db.Column(db.Float)
    cer_first_name = db.Column(db.Float)
    cer_last_name = db.Column(db.Float)
    cer_dob = db.Column(db.Float)
    cer_address = db.Column(db.Float)
    cer_avg = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
