import os
import pandas as pd
from flask import Blueprint, render_template, redirect, url_for, flash, current_app, jsonify
from flask_login import current_user
from werkzeug.utils import secure_filename
from automation.bot import descargar_archivo, bot_status
from forms.forms import CSVForm 
from services.etl_service import import_csv_to_db


etl_bp = Blueprint('etl', __name__)


@etl_bp.route('/etl', methods=['GET', 'POST'])
def etl():
    
    form = CSVForm()
    
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    if not form.validate_on_submit():
        return render_template('etl.html', form=form)
        
    file = form.csv.data
    filename = secure_filename(file.filename)
    
    # 📁 1️⃣ Determinar y asegurar carpeta de subida
    upload_folder = current_app.config.get(
        'UPLOAD_FOLDER',
        os.path.join(current_app.root_path, 'static', 'uploads')
    )
    os.makedirs(upload_folder, exist_ok=True)
    
    # 📄 2️⃣ Guardar el archivo en la carpeta de uploads
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    print(f"[INFO] Archivo guardado en: {file_path}")  # Log útil
    
    # 🧮 3️⃣ Leer CSV con pandas
    try:
        try:
            # Intentar UTF-8 primero
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            # Si falla, intentar codificaciones comunes en español
            try:
                df = pd.read_csv(file_path, encoding='latin-1')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='cp1252')
    except Exception as e:
        flash(f"Error al leer el archivo CSV: {e}", "danger")
        return redirect(url_for('etl.etl'))
    
    # 🧠 Insertar datos en la base de datos
    try:
        import_csv_to_db(df)
        
        # Borrar el archivo después de procesar (opcional, pero recomendado)
        #os.remove(file_path)
        # print(f"[INFO] Archivo procesado y eliminado: {file_path}")
    except Exception as e:
        flash(f"❌ Error al procesar el CSV: {e}", "danger")
        print(f"[ERROR] Falló la importación del CSV: {e}")
        
    # 🔁 Redirigir al dashboard
    return redirect(url_for('daily.daily'))


@etl_bp.route("/run-bot", methods=["POST"])
def run_bot_manual():
    
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    if bot_status["running"]:
        return jsonify({"status": "already_running"}), 409

    try:
        descargar_archivo()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@etl_bp.route("/bot-status", methods=["GET"])
def get_bot_status():
    
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    return jsonify({
        "running": bot_status["running"],
        "last_run": bot_status["last_run"].strftime("%d-%m %H:%M:%S") if bot_status["last_run"] else None,
        "last_error": bot_status["last_error"]
    })