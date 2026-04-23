import logging
import os
import shutil

import pandas as pd
from flask import Blueprint, render_template, redirect, url_for, flash, current_app, jsonify, request
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf
from wtforms import ValidationError
from werkzeug.utils import secure_filename

from automation.bot import descargar_archivo, bot_status
from forms.forms import CSVForm
from models.models import BotLog, db
from services.etl_service import import_csv_to_db
from services.log_service import registrar_log

logger = logging.getLogger(__name__)

etl_bp = Blueprint("etl", __name__)

ENCODINGS = ["utf-8", "latin-1", "cp1252"]


def _leer_csv(file_path):
    for enc in ENCODINGS:
        try:
            return pd.read_csv(file_path, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("No se pudo leer el CSV con ninguna codificación soportada.")


def _archivar_csv(file_path):
    """Mueve el CSV subido manualmente al directorio de archivo."""
    archive_dir = current_app.config.get("ARCHIVE_FOLDER")
    os.makedirs(archive_dir, exist_ok=True)
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(archive_dir, f"{ts}_{os.path.basename(file_path)}")
    shutil.move(file_path, dest)
    logger.info("CSV archivado en: %s", dest)


@etl_bp.route("/etl", methods=["GET", "POST"])
@login_required
def etl():
    form = CSVForm()

    if not form.validate_on_submit():
        logs = (
            BotLog.query
            .order_by(BotLog.timestamp.desc())
            .limit(20)
            .all()
        )
        return render_template("etl.html", form=form, logs=logs)

    file = form.csv.data
    filename = secure_filename(file.filename)

    upload_folder = current_app.config.get(
        "UPLOAD_FOLDER",
        os.path.join(current_app.root_path, "static", "uploads"),
    )
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    logger.info("CSV subido manualmente: %s", file_path)

    try:
        df = _leer_csv(file_path)
    except Exception as exc:
        flash(f"Error al leer el archivo CSV: {exc}", "danger")
        return redirect(url_for("etl.etl"))

    try:
        inserted, skipped, updated = import_csv_to_db(df)
        flash(
            f"Archivo procesado — {inserted} insertados, {updated} actualizados, {skipped} omitidos.",
            "success",
        )
        registrar_log(
            tipo="csv_manual",
            estado="exito",
            mensaje=f"Archivo: {filename}",
            insertados=inserted,
            actualizados=updated,
            omitidos=skipped,
        )
        _archivar_csv(file_path)
    except Exception as exc:
        flash(f"Error al procesar el CSV: {exc}", "danger")
        logger.error("Error importando CSV %s: %s", filename, exc)
        registrar_log(tipo="csv_manual", estado="error", mensaje=f"{filename} — {exc}")

    return redirect(url_for("daily.daily"))


@etl_bp.route("/run-bot", methods=["POST"])
@login_required
def run_bot_manual():
    # Validar CSRF del header enviado por JS
    try:
        validate_csrf(request.headers.get("X-CSRFToken"))
    except ValidationError:
        return jsonify({"status": "error", "message": "Token CSRF inválido"}), 400

    if bot_status["running"]:
        return jsonify({"status": "already_running"}), 409

    try:
        descargar_archivo()
        return jsonify({"status": "success"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@etl_bp.route("/bot-status", methods=["GET"])
@login_required
def get_bot_status():
    return jsonify({
        "running": bot_status["running"],
        "last_run": (
            bot_status["last_run"].strftime("%d-%m %H:%M:%S")
            if bot_status["last_run"] else None
        ),
        "last_error": bot_status["last_error"],
    })
