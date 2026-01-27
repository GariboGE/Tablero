from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from services.payments import get_payments_data


payments_bp = Blueprint('payments', __name__)


@payments_bp.route('/payments', methods=['GET', 'POST'])
def payments():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    data = get_payments_data()
    return render_template('payments.html', data=data)
    
