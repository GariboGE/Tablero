import fcntl
import logging
import os

from flask import Flask, redirect, url_for, request, jsonify
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from dotenv import load_dotenv

from models.models import db, User, MetaMensual
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.etl import etl_bp
from routes.daily import daily_bp
from routes.payments import payments_bp
from routes.accounting import accounting_bp
from routes.email import email_bp
from routes.admin import admin_bp
from automation.bot import descargar_archivo

load_dotenv()

# Logging global — INFO a stdout, formato con timestamp
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

mail = Mail()
csrf = CSRFProtect()

# Valores por defecto para las metas mensuales
_METAS_DEFAULT = [
    ("Tijuana",   1000000.00),
    ("Mexicali",  500000.00),
    ("Ensenada",  300000.00),
]


def _seed_metas(app):
    """Siembra las metas del mes actual si la tabla está vacía para ese mes."""
    now = datetime.now()
    with app.app_context():
        if not MetaMensual.query.filter_by(mes=now.month, anio=now.year).first():
            for sucursal, monto in _METAS_DEFAULT:
                db.session.add(MetaMensual(
                    sucursal=sucursal, mes=now.month, anio=now.year, monto=monto
                ))
            db.session.commit()
            logger.info("Metas mensuales sembradas para %d/%d.", now.month, now.year)


def start_scheduler(app):
    if app.config.get("TESTING"):
        return

    lock_path = "/tmp/tablero_scheduler.lock"
    try:
        lock_fh = open(lock_path, "w")
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        logger.info("Scheduler ya está corriendo en otro worker — omitiendo.")
        return

    scheduler = BackgroundScheduler(timezone="America/Tijuana")

    def job_wrapper():
        now = datetime.now()
        if now.weekday() >= 5:
            logger.info("[SCHEDULER] Fin de semana — omitiendo ejecución.")
            return
        if not (8 <= now.hour <= 19):
            logger.info("[SCHEDULER] Fuera de horario laboral — omitiendo ejecución.")
            return
        with app.app_context():
            try:
                logger.info("[SCHEDULER] Ejecutando bot...")
                descargar_archivo()
            except Exception as exc:
                logger.error("[SCHEDULER] Error: %s", exc)

    scheduler.add_job(
        func=job_wrapper,
        trigger="cron",
        minute="*/30",
        hour="9-18",
        day_of_week="mon-fri",
        id="descarga_archivo_job",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=900,
    )

    scheduler.start()
    import atexit
    atexit.register(lambda: scheduler.shutdown(wait=False))
    logger.info("Scheduler iniciado.")


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    with app.app_context():
        db.create_all()

        admin_username = os.getenv("ADMIN_USER")
        admin_password = os.getenv("ADMIN_PASSWORD")
        if admin_username and not User.query.filter_by(username=admin_username).first():
            db.session.add(User(username=admin_username, password=generate_password_hash(admin_password)))
            logger.info("Usuario admin creado: %s", admin_username)

        bot_username = os.getenv("BOT_USER")
        bot_password = os.getenv("BOT_PASSWORD")
        if bot_username and not User.query.filter_by(username=bot_username).first():
            db.session.add(User(username=bot_username, password=generate_password_hash(bot_password)))
            logger.info("Usuario bot creado: %s", bot_username)

        db.session.commit()

    _seed_metas(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        # Rutas de API devuelven JSON 401; el resto redirige al login
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"error": "No autenticado"}), 401
        return redirect(url_for("auth.login"))

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("daily.daily"))
        return redirect(url_for("auth.login"))

    @app.errorhandler(404)
    def page_not_found(e):
        return redirect(url_for("daily.daily"))

    app.register_blueprint(auth_bp,       url_prefix="/auth")
    app.register_blueprint(dashboard_bp,  url_prefix="/dashboard")
    app.register_blueprint(daily_bp,      url_prefix="/daily")
    app.register_blueprint(etl_bp,        url_prefix="/etl")
    app.register_blueprint(payments_bp,   url_prefix="/payments")
    app.register_blueprint(accounting_bp, url_prefix="/accounting")
    app.register_blueprint(email_bp,      url_prefix="/email")
    app.register_blueprint(admin_bp,      url_prefix="/admin")

    start_scheduler(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
