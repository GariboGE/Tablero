import os
import pandas as pd
from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename
from forms.forms import CSVForm
from services.etl_service import import_csv_to_db

etl_bp = Blueprint('etl', __name__)


@etl_bp.route('/etl', methods=['GET', 'POST'])
def etl():
    form = CSVForm()
    
    if current_user.is_authenticated:
        if form.validate_on_submit():
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
                flash("✅ Archivo procesado y datos cargados correctamente en la base de datos.", "success")
            except Exception as e:
                flash(f"❌ Error al procesar el CSV: {e}", "danger")
                print(f"[ERROR] Falló la importación del CSV: {e}")

            # 🔁 Redirigir al dashboard
            return redirect(url_for('dashboard.dashboard'))
        return render_template('etl.html', form=form)
    
    return redirect(url_for('auth.login'))