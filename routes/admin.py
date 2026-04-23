import io
import logging
import pandas as pd
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models.models import db, MetaMensual, EmailDestinatario
from forms.forms import EmptyForm

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__)

_MESES_ES = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
}


def _parsear_archivo_metas(archivo, es_xlsx):
    contenido = archivo.read()
    if es_xlsx:
        df = pd.read_excel(io.BytesIO(contenido), header=0)
    else:
        df = None
        for enc in ('utf-8', 'latin-1', 'cp1252'):
            try:
                df = pd.read_csv(io.StringIO(contenido.decode(enc)), header=0)
                break
            except UnicodeDecodeError:
                continue
        if df is None:
            raise ValueError("No se pudo decodificar el archivo CSV.")

    resultados = []
    for _, row in df.iterrows():
        sucursal = str(row.iloc[0]).strip() if row.iloc[0] is not None else ""
        if not sucursal or sucursal.lower() in ('none', 'nan', ''):
            continue
        for col in df.columns[1:]:
            mes_num = _MESES_ES.get(str(col).strip().lower())
            if mes_num is None:
                continue
            try:
                monto = float(row[col])
            except (TypeError, ValueError):
                continue
            if monto > 0:
                resultados.append((sucursal, mes_num, monto))
    return resultados


# ── Metas mensuales ────────────────────────────────────────────

@admin_bp.route("/goals", methods=["GET", "POST"])
@login_required
def goals():
    form = EmptyForm()

    if form.validate_on_submit():
        sucursal = request.form.get("sucursal", "").strip()
        try:
            mes   = int(request.form.get("mes", 0))
            anio  = int(request.form.get("anio", 0))
            monto = float(request.form.get("monto", 0))
        except (ValueError, TypeError):
            flash("Datos numéricos inválidos.", "danger")
            return redirect(url_for("admin.goals"))

        if not sucursal or not (1 <= mes <= 12) or anio < 2020 or monto < 0:
            flash("Revisa los datos del formulario.", "danger")
            return redirect(url_for("admin.goals"))

        meta = MetaMensual.query.filter_by(sucursal=sucursal, mes=mes, anio=anio).first()
        if meta:
            meta.monto = monto
        else:
            meta = MetaMensual(sucursal=sucursal, mes=mes, anio=anio, monto=monto)
            db.session.add(meta)

        db.session.commit()
        flash(f"Meta guardada: {sucursal} — {mes}/{anio} → ${monto:,.0f}", "success")
        return redirect(url_for("admin.goals"))

    from datetime import datetime
    now = datetime.now()

    metas = (
        MetaMensual.query
        .order_by(MetaMensual.anio.desc(), MetaMensual.mes.desc(), MetaMensual.sucursal)
        .all()
    )
    return render_template(
        "admin/goals.html",
        form=form,
        metas=metas,
        mes_actual=now.month,
        anio_actual=now.year,
    )


@admin_bp.route("/goals/<int:id>/delete", methods=["POST"])
@login_required
def delete_goal(id):
    form = EmptyForm()
    if form.validate_on_submit():
        meta = MetaMensual.query.get_or_404(id)
        db.session.delete(meta)
        db.session.commit()
        flash("Meta eliminada.", "success")
    return redirect(url_for("admin.goals"))


@admin_bp.route("/goals/upload", methods=["POST"])
@login_required
def upload_goals():
    form = EmptyForm()
    if not form.validate_on_submit():
        flash("Error de seguridad en el formulario.", "danger")
        return redirect(url_for("admin.goals"))

    archivo = request.files.get("archivo")
    try:
        anio = int(request.form.get("anio_upload", 0))
    except (ValueError, TypeError):
        anio = 0

    if not archivo or not archivo.filename:
        flash("No se seleccionó ningún archivo.", "danger")
        return redirect(url_for("admin.goals"))

    if not (1 <= anio <= 2099 and anio >= 2020):
        flash("Año inválido.", "danger")
        return redirect(url_for("admin.goals"))

    nombre = archivo.filename.lower()
    es_xlsx = nombre.endswith('.xlsx')
    if not (es_xlsx or nombre.endswith('.csv')):
        flash("Solo se aceptan archivos .xlsx o .csv.", "danger")
        return redirect(url_for("admin.goals"))

    try:
        filas = _parsear_archivo_metas(archivo, es_xlsx)
    except Exception as e:
        logger.exception("Error al parsear archivo de metas")
        flash(f"Error al procesar el archivo: {e}", "danger")
        return redirect(url_for("admin.goals"))

    if not filas:
        flash("El archivo no contiene datos válidos.", "warning")
        return redirect(url_for("admin.goals"))

    insertados = actualizados = 0
    for sucursal, mes, monto in filas:
        meta = MetaMensual.query.filter_by(sucursal=sucursal, mes=mes, anio=anio).first()
        if meta:
            meta.monto = monto
            actualizados += 1
        else:
            db.session.add(MetaMensual(sucursal=sucursal, mes=mes, anio=anio, monto=monto))
            insertados += 1
    db.session.commit()
    flash(f"Metas importadas para {anio}: {insertados} nuevas, {actualizados} actualizadas.", "success")
    return redirect(url_for("admin.goals"))


# ── Destinatarios de email ─────────────────────────────────────

@admin_bp.route("/recipients", methods=["GET", "POST"])
@login_required
def recipients():
    form = EmptyForm()

    if form.validate_on_submit():
        accion = request.form.get("accion")

        if accion == "agregar":
            email = request.form.get("email", "").strip().lower()
            nombre = request.form.get("nombre", "").strip()

            if not email or "@" not in email or "." not in email.split("@")[-1]:
                flash("Dirección de email inválida.", "danger")
                return redirect(url_for("admin.recipients"))

            if EmailDestinatario.query.filter_by(email=email).first():
                flash("El destinatario ya existe.", "warning")
                return redirect(url_for("admin.recipients"))

            db.session.add(EmailDestinatario(email=email, nombre=nombre, activo=True))
            db.session.commit()
            flash(f"Destinatario agregado: {email}", "success")

        return redirect(url_for("admin.recipients"))

    destinatarios = (
        EmailDestinatario.query
        .order_by(EmailDestinatario.activo.desc(), EmailDestinatario.nombre)
        .all()
    )
    return render_template("admin/recipients.html", form=form, destinatarios=destinatarios)


@admin_bp.route("/recipients/<int:id>/toggle", methods=["POST"])
@login_required
def toggle_recipient(id):
    form = EmptyForm()
    if form.validate_on_submit():
        dest = EmailDestinatario.query.get_or_404(id)
        dest.activo = not dest.activo
        db.session.commit()
        estado = "activado" if dest.activo else "desactivado"
        flash(f"Destinatario {estado}: {dest.email}", "success")
    return redirect(url_for("admin.recipients"))


@admin_bp.route("/recipients/<int:id>/delete", methods=["POST"])
@login_required
def delete_recipient(id):
    form = EmptyForm()
    if form.validate_on_submit():
        dest = EmailDestinatario.query.get_or_404(id)
        db.session.delete(dest)
        db.session.commit()
        flash("Destinatario eliminado.", "success")
    return redirect(url_for("admin.recipients"))
