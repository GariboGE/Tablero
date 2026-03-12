from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from models.models import db, User
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.etl import etl_bp
from routes.daily import daily_bp
from routes.payments import payments_bp
from routes.accounting import accounting_bp
from routes.email import email_bp
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
from automation.bot import descargar_archivo
from datetime import datetime
from flask_mail import Mail
import os


load_dotenv()
mail = Mail()

def start_scheduler(app):
    scheduler = BackgroundScheduler(timezone="America/Tijuana")

    def job_wrapper():
        now = datetime.now()
        print(f"[SCHEDULER] Hora actual: {now}")
        
        if now.weekday() >= 5:
            print("[SCHEDULER] No se ejecuta el bot en fines de semana.")
            return
        if not (8 <= now.hour <= 19):
            print("[SCHEDULER] No se ejecuta el bot fuera del horario laboral.")
            return
        
        with app.app_context():
            try:
                print("[SCHEDULER] Ejecutando bot...")
                descargar_archivo()
            except Exception as e:
                print(f"[SCHEDULER ERROR] {e}")

    scheduler.add_job(
        func=job_wrapper,
        # next_run_time=datetime.now(),
        trigger="cron",
        minute="*/30",
        hour="9-18",
        day_of_week="mon-fri",
        id="descarga_archivo_job",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=900
    )

    scheduler.start()
    import atexit
    atexit.register(lambda: scheduler.shutdown())


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Configuración de la base de datos
    db.init_app(app)
    
    # Inicializar Flask-Mail
    mail.init_app(app)
    
    # Inicializar base de datos en el contexto de la app
    with app.app_context():
        db.create_all()
        # Crear usuario admin y bot si no existen
        admin_username = os.getenv('ADMIN_USER')
        admin_password = os.getenv('ADMIN_PASSWORD')
        existing_admin = User.query.filter_by(username=admin_username).first()
        
        bot_username = os.getenv('BOT_USER')
        bot_password = os.getenv('BOT_PASSWORD')
        existing_bot = User.query.filter_by(username=bot_username).first()

        if not existing_admin:
            hashed_pw = generate_password_hash(admin_password)
            admin_user = User(username=admin_username, password=hashed_pw)
            db.session.add(admin_user)
        if not existing_bot:
            hashed_pw = generate_password_hash(bot_password)
            bot_user = User(username=bot_username, password=hashed_pw)
            db.session.add(bot_user)
            db.session.commit()
            print(f"Usuario admin creado: {admin_username}/{admin_password}")
            print(f"Usuario bot creado: {bot_username}/{bot_password}")
        else:
            print("Usuario admin ya existe")
            print("Usuario bot ya existe")

    # Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)


    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))


    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('daily.daily'))
        return redirect(url_for('auth.login'))


    @app.errorhandler(404)
    def page_not_found(e):
        return redirect(url_for('daily.daily'))

    # Registrar Blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(daily_bp, url_prefix='/daily')
    app.register_blueprint(etl_bp, url_prefix='/etl')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    app.register_blueprint(accounting_bp, url_prefix='/accounting')
    app.register_blueprint(email_bp, url_prefix='/email')
    
    start_scheduler(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
