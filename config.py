import os


class Config:
    # Base settings
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
    
    # App secrets
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback_secret_key')
    
    # Data ETL settings
    DATA_ETL_PATH = os.getenv('DATA_ETL_PATH', 'etl')