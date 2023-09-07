import re

from flask_jwt_extended import jwt_required, create_access_token, verify_jwt_in_request, get_jwt
from functools import wraps

import config
from app.models.user import Role

# from app import app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature


# VERIFY IF TALAN EMAIL
def is_talan_email(email):
    """
    checks if email has the specified pattern 
    :param email:
    :return:
    """
    regex_talan = r'^[a-zA-Z0-9._%+-]+@talan\.com$'
    return re.match(regex_talan, email)


def is_strong_password(password):
    """
    This function checks if a password has a minimum length and only alphanumeric or special characters
    the password should have at least one uppercase, one lowercase, one digit and one special
    :param password: the password to be checked
    :return:
    """

    min_length = 12
    allowed_special_chars = "!@#$%^&*()_+{}|:<>?,-=[]\;'./`~"

    # Check for password length (at least 8 characters)
    if len(password) < min_length:
        return False

    # Check that password only contains alphanumeric characters and allowed special characters
    if not all(char.isalnum() or char in allowed_special_chars for char in password):
        return False

    # Check for at least one uppercase letter
    if not any(char.isupper() for char in password):
        return False

    # Check for at least one lowercase letter
    if not any(char.islower() for char in password):
        return False

    # Check for at least one digit
    if not any(char.isdigit() for char in password):
        return False

    # Check for at least one special character (allowed)
    if not any(char in allowed_special_chars for char in password):
        return False

    return True


# VERIFICATION TOKENS GENERATION AND CHECKING
def generate_email_token(email):
    """
    generates an itsdangerous token containing the hashed email
    :param email: 
    :return: 
    """
    from app import app
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['VERIFICATION_TOKEN_SALT'])


def confirm_email_token(token):
    """
    verifies the received token
    :param token: itsdangerous token
    :return: dehashed email OR False
    """
    from app import app
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    try:

        email = serializer.loads(
            token,
            salt=app.config['VERIFICATION_TOKEN_SALT'],
            max_age=app.config['VERIFICATION_TOKEN_AGE']
        )

        return email
    except (SignatureExpired, BadSignature):
        print("token_confimation failed")
        return False


# ADMIN REQUIRED DECORATOR
def admin_required(f):
    """
    Decorator function that checks if the jwt token is from user having only the role of admin (security measure)
    :param f:
    :return:
    """
    @wraps(f)
    def wrapper(*args, **kwargs):

        # verifies if token is valid (can replace token required
        #verify_jwt_in_request()

        # Check if token has required claims
        claims = get_jwt()['claims']
        if not claims or 'roles' not in claims:
            return {'message': 'Invalid token'}, 401

        # Check that the "admin" role is present in the list of roles
        roles = claims['roles']
        if Role.ADMIN.value not in roles:
            return {'message': 'Admin role required'}, 403

        if any(role != Role.ADMIN.value for role in roles):
            return {'message': 'Invalid token (roles)'}, 400


        # Call the wrapped function if all checks pass
        return f(*args, **kwargs)

    return wrapper


# TL REQUIRED DECORATOR
def team_leader_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # verifies if token is valid (can replace token required
        #verify_jwt_in_request()


        # Check if token has required claims
        claims = get_jwt()['claims']
        if not claims or 'roles' not in claims:
            return {'message': 'Invalid token'}, 401

        # Check that the "admin" role is present in the list of roles
        roles = claims['roles']
        if Role.TEAM_LEADER.value not in roles:
            return {'message': 'Team Leader role required'}, 403

        # Call the wrapped function if all checks pass
        return f(*args, **kwargs)

    return wrapper
