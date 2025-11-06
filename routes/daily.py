from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import current_user
from services.daily_service import get_daily_data


daily_bp = Blueprint('daily', __name__)


@daily_bp.route('/daily', methods=['GET', 'POST'])
def daily():
    if current_user.is_authenticated:
        data = get_daily_data()
        return render_template('daily.html', data=data)
    
    return redirect(url_for('auth.login'))