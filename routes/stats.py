from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

stats_bp = Blueprint('stats', __name__)

# Exemple de route
@stats_bp.route("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    return jsonify({"user_id": user_id})
