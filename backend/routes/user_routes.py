from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database.models import db, User

user_bp = Blueprint("user", __name__)

@user_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        return jsonify({"error": "Missing fields"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    hashed_pw = generate_password_hash(password)
    user = User(username=username, email=email, password_hash=hashed_pw)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User registered successfully!"})

@user_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    # 🧩 ขั้นแรก: ตรวจว่ามี email หรือไม่
    user = User.query.filter_by(email=email).first()

    # 🟠 ถ้าไม่พบผู้ใช้เลย
    if user is None:
        return jsonify({"error": "User not found"}), 404

    # 🟡 ถ้ามี user แต่รหัสผิด
    if not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid password"}), 401

    # 🟢 ถ้าทุกอย่างถูกต้อง
    return jsonify({
        "message": "Login successful!",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 200

