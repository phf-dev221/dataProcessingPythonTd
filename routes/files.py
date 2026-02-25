import io
import traceback

import numpy as np
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import db
from models import History
from models.user import User
from services.file_service import load_file, process_dataframe, convert_file, analyze_dataframe

files_bp = Blueprint("files", __name__)

@files_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']

    try:
        df = load_file(file)

        # ── Diagnostic AVANT nettoyage ──────────────────────────
        diagnostic = analyze_dataframe(df)

        cleaned_df, rows_cleaned = process_dataframe(df)
        rows_cleaned = int(rows_cleaned)

        user_id = get_jwt_identity()
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.totalFilesProcessed += 1
        user.totalRowsCleaned += rows_cleaned

        history = History(
            user_id=user_id,
            filename=file.filename,
            action="clean",
            rows=int(rows_cleaned)
        )
        db.session.add(history)
        db.session.commit()

        return jsonify({
            "message": "File processed successfully",
            "rows_cleaned": rows_cleaned,
            "total_files_processed": user.totalFilesProcessed,
            "total_rows_cleaned": user.totalRowsCleaned,
            "data_preview": cleaned_df.head(20).to_dict(orient="records"),
            "diagnostic": diagnostic,           # <── stats avant/après
        })

    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@files_bp.route("/diagnose", methods=["POST"])
@jwt_required()
def diagnose_file():
    """
diagnoz ici
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']

    try:
        df = load_file(file)
        diagnostic = analyze_dataframe(df)
        return jsonify(diagnostic)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@files_bp.route("/download", methods=["POST"])
@jwt_required()
def download_cleaned():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    extension = file.filename.split('.')[-1].lower()

    try:
        df = load_file(file)
        cleaned_df, _ = process_dataframe(df)

        output = io.BytesIO()

        if extension == 'csv':
            cleaned_df.to_csv(output, index=False)
            mimetype = "text/csv"
            download_name = f"cleaned_{file.filename}"

        elif extension == 'xlsx':
            cleaned_df.to_excel(output, index=False, engine="openpyxl")
            mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            download_name = f"cleaned_{file.filename}"

        elif extension == 'json':
            output.write(cleaned_df.to_json(orient="records", indent=2).encode("utf-8"))
            mimetype = "application/json"
            download_name = f"cleaned_{file.filename}"

        else:
            return jsonify({"error": "Unsupported format"}), 400

        output.seek(0)
        return send_file(output, mimetype=mimetype, as_attachment=True, download_name=download_name)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@files_bp.route("/convert", methods=["POST"])
@jwt_required()
def convert():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    conversion_type = request.form.get('conversion_type')

    if not conversion_type:
        return jsonify({"error": "No conversion type provided"}), 400

    valid_types = [
        'csv-to-excel', 'excel-to-json', 'csv-to-json',
        'json-to-csv', 'excel-to-csv', 'json-to-excel',
        'xml-to-csv', 'xml-to-json', 'xml-to-excel'
    ]
    if conversion_type not in valid_types:
        return jsonify({"error": "Invalid conversion type"}), 400

    try:
        output, mimetype, filename = convert_file(file, conversion_type)

        user_id = get_jwt_identity()
        user = db.session.get(User, user_id)
        user.totalFilesProcessed = int(user.totalFilesProcessed or 0) + 1

        history = History(
            user_id=user_id,
            filename=file.filename,
            action="convert",
            rows=0
        )
        db.session.add(history)
        db.session.commit()

        return send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": str(e)}), 500