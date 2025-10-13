from flask import Flask, jsonify
from flask_cors import CORS 
from config import Config
from database import db
from database.models import User, OcrResult, CerResult
from werkzeug.security import generate_password_hash, check_password_hash
from routes.user_routes import user_bp
from routes.ocr_routes import ocr_bp
from flask import send_from_directory
import os

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# เชื่อม SQLAlchemy เข้ากับ Flask
db.init_app(app)

# Register routes
app.register_blueprint(user_bp)
app.register_blueprint(ocr_bp)

@app.route("/")
def index():
    return jsonify({"message": "Backend connected to Database successfully!"})

@app.route("/add_user")
def add_user():
    hashed_pw = generate_password_hash("123456")   # กำหนด password hash
    user = User(username="Test User", email="test@example.com", password_hash=hashed_pw)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User added!"})


@app.route("/list_users")
def list_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "username": u.username, "email": u.email} for u in users])

# ===== เสิร์ฟรูปภาพในโฟลเดอร์ uploads =====
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    print("[DEBUG] Serving file:", os.path.join(upload_dir, filename))
    return send_from_directory(upload_dir, filename)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # สร้าง table (ถ้าไม่มี)
    app.run(debug=True, port=5000)