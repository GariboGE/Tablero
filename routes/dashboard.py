from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import current_user
from services.dashboard_service import get_dashboard_data


dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if current_user.is_authenticated:
        data = get_dashboard_data()
        return render_template('dashboard.html', data=data)
    
    return redirect(url_for('auth.login'))
