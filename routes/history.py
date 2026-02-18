from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from datetime import datetime, timedelta
from sqlalchemy import func

from database import db
from models.history import History

history_bp = Blueprint("history", __name__)

@history_bp.route("/", methods=["GET"])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    entries = History.query.filter_by(user_id=user_id)\
                .order_by(History.created_at.desc())\
                .limit(20).all()

    if not entries:
        return jsonify({"message": "No entries found."}), 404

    return jsonify([{
        "id":         h.id,
        "filename":   h.filename,
        "action":     h.action,
        "rows":       h.rows,
        "created_at": h.created_at.strftime("%b %d, %Y")
    } for h in entries])


@history_bp.route("/chart", methods=["GET"])
@jwt_required()
def get_chart_data():
    user_id = get_jwt_identity()

    # 7 derniers jours
    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=6)

    results = db.session.query(
        func.date(History.created_at).label('date'),
        func.count(History.id).label('files')
    ).filter(
        History.user_id == user_id,
        func.date(History.created_at) >= seven_days_ago
    ).group_by(func.date(History.created_at)).all()

    # Construire les 7 jours même si pas d'activité ce jour là
    data = {}
    for r in results:
        data[r.date] = r.files

    chart = []
    for i in range(7):
        day = (seven_days_ago + timedelta(days=i)).isoformat()
        chart.append({"date": day, "files": data.get(day, 0)})

    return jsonify(chart)