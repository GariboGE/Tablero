from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from services.dashboard_service import get_dashboard_data


dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    else:
        return redirect(url_for('auth.login'))


@dashboard_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    data = get_dashboard_data()
    return render_template('dashboard.html', data=data)