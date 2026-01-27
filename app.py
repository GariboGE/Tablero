from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from models.models import db, User
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp 
from routes.etl import etl_bp
from routes.daily import daily_bp
from routes.payments import payments_bp
from routes.accounting import accounting_bp
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Configuración de la base de datos
    db.init_app(app)

    # Inicializar base de datos en el contexto de la app
    with app.app_context():
        db.create_all()
        
        admin_username = os.getenv('ADMIN_USER')
        admin_password = os.getenv('ADMIN_PASSWORD')
        existing_admin = User.query.filter_by(username=admin_username).first()

        if not existing_admin:
            hashed_pw = generate_password_hash(admin_password)
            admin_user = User(username=admin_username, password=hashed_pw)
            db.session.add(admin_user)
            db.session.commit()
            print(f"Usuario admin creado: {admin_username}/{admin_password}")
        else:
            print("Usuario admin ya existe")
    
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

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
