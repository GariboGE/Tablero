import pytest
from app import create_app
from models.models import db as _db


@pytest.fixture(scope="session")
def app():
    """App con base de datos SQLite en memoria, solo para tests."""
    test_app = create_app()
    test_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret",
    })
    with test_app.app_context():
        _db.create_all()
        yield test_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="session")
def db(app):
    return _db


@pytest.fixture()
def client(app):
    return app.test_client()
