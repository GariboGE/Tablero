import logging
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from models.models import EmailDestinatario
from services.email_service import send_email

logger = logging.getLogger(__name__)

email_bp = Blueprint("email", __name__)


@email_bp.route("/email", methods=["GET", "POST"])
@login_required
def email():
    if request.method == "POST":
        try:
            # Destinatarios desde checkboxes de la BD
            selected_ids = request.form.getlist("recipient_ids")
            recipients = []

            if selected_ids:
                dest_db = EmailDestinatario.query.filter(
                    EmailDestinatario.id.in_(selected_ids),
                    EmailDestinatario.activo == True,
                ).all()
                recipients = [d.email for d in dest_db]

            # Destinatarios adicionales escritos manualmente
            manual = request.form.get("recipients", "").strip()
            if manual:
                recipients += [r.strip() for r in manual.split(",") if r.strip()]

            if not recipients:
                flash("Debes seleccionar o ingresar al menos un destinatario.", "warning")
                return redirect(url_for("email.email"))

            send_email(
                subject="Envío de imágenes del corte del día",
                recipients=recipients,
                body=None,
                html=None,
            )
            flash(f"Email enviado a {len(recipients)} destinatario(s).", "success")

        except Exception as exc:
            logger.error("Error al enviar email: %s", exc)
            flash(f"Error al enviar email: {exc}", "danger")

        return redirect(url_for("email.email"))

    db_recipients = (
        EmailDestinatario.query
        .order_by(EmailDestinatario.activo.desc(), EmailDestinatario.nombre)
        .all()
    )
    return render_template("email.html", db_recipients=db_recipients)
