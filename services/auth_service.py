from werkzeug.security import generate_password_hash
from models.models import db, User


def get_user_by_username(username):
    """
    Retrieve a user from the database by their username.

    Args:
        username (str): The username of the user to search for.

    Returns:
        User: The User object if found, otherwise None.
    """
    return db.session.query(User).filter_by(username=username).first()


def create_user(username, password):
    """
    Create a new user in the database with a hashed password.

    This function checks if a user with the provided username already exists in the database.
    If not, it hashes the password, creates a new `User` instance, and commits it to the database.

    Args:
        username (str): The desired username for the new user.
        password (str): The password for the new user account.

    Returns:
        bool: True if the user is successfully created, False if the username already exists.
    """
    existing_user = get_user_by_username(username)
    if existing_user:
        return False
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return True
