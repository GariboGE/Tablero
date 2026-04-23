import os


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
    ARCHIVE_FOLDER = os.path.join(BASE_DIR, 'static/uploads/archive')

    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback_secret_key')

    DATA_ETL_PATH = os.getenv('DATA_ETL_PATH', 'etl')

    MAIL_SERVER = os.getenv('MAIL_SERVER', 'az1-ls15.a2hosting.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 465))
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'true').lower() == 'true'
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'false').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'egaribo@credinspira.mx')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'egaribo@credinspira.mx')
