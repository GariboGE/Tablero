from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user


accounting_bp = Blueprint('accounting', __name__)


@accounting_bp.route('/accounting', methods=['GET', 'POST'])
def accounting():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    return render_template('accounting.html')
    
