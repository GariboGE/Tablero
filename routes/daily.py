from flask import Blueprint, render_template
from flask_login import login_required
from services.daily_service import get_daily_data


daily_bp = Blueprint("daily", __name__)


@daily_bp.route("/daily", methods=["GET"])
@login_required
def daily():
    data = get_daily_data()
    return render_template("daily.html", data=data)
