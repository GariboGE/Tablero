from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user
from services.email_service import send_email


email_bp = Blueprint('email', __name__)


@email_bp.route('/email', methods=['GET', 'POST'])
def email():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            raw_recipients = request.form.get('recipients')
            recipients = [r.strip() for r in raw_recipients.split(',') if r.strip()]
        
            send_email(
                subject="Envío de imágenes del corte del día",
                recipients=recipients,
                body=None,
                html=None,
            )
            flash("Email sent successfully", "success")
            
        except Exception as e:
            flash(f"Error al enviar email: {e}", "danger")
        
        return redirect(url_for('email.email'))

    return render_template('email.html')

