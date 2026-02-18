from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user import User
from database import db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email et mot de passe requis"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Utilisateur déjà existant"}), 409

    user = User(email=data["email"])
    user.set_password(data["password"])
    user.name = data.get("name")
    user.joined_date = data.get("joinedDate")
    user.total_files_processed = data.get("totalFilesProcessed", 0)
    user.total_rows_cleaned = data.get("totalRowsCleaned", 0)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Utilisateur créé", "success": True}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    user = User.query.filter_by(email=data.get("email")).first()

    if not user or not user.check_password(data.get("password")):
        return jsonify({"error": "Identifiants invalides"}), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "access_token": access_token,
        "user": {
            "id": user.id,
            "email": user.email
        }
    })

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "joinedDate": user.joinedDate.isoformat(),
        "totalFilesProcessed": int(user.totalFilesProcessed or 0),
        "totalRowsCleaned": int(user.totalRowsCleaned or 0),
    })

@auth_bp.route("/logout", methods=["GET"])
@jwt_required()
def logout():
    jti = get_jwt_identity()

