from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, redirect, url_for, jsonify, render_template
from flask_jwt_extended import create_access_token, jwt_required, unset_jwt_cookies, get_jwt, decode_token
from mongoengine import DoesNotExist
from werkzeug.exceptions import BadRequest, Unauthorized

from app.models.registration_requests import RegistrationRequest
from app.utils.mail import send_email
from app.models.revoked_tokens import RevokedToken
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash



from app.routes.api.middleware import confirm_email_token, generate_email_token, is_talan_email, is_strong_password

####### Vaariables ########
auth = Blueprint('auth', __name__)


####### Routes ########

@auth.route('/login', methods=['POST'])
def login():
    """
    Checks the input, email conformity to regex, if user and password match, before login
    :return: 200, jwt token, user data  OR 400 error message
    """

    if request.is_json:
        email = request.json['email']
        password = request.json['password']

    if not email or not password:
        return jsonify({"message": "Missing credentials"}), 400

    # email must be a talan email
    if not is_talan_email(email):
        return jsonify(message='Invalid email address'), 400

    # Change return to 'incorrect credentials' only
    try:
        user = User.objects(email=email).first()
        if user and check_password_hash(user.password, password):
            # access token creation, to include more information in token, add it to user_data dictionary
            roles = [role.value for role in user.roles]
            claims = {'roles': roles}

            # automatically adds expiration time from the config
            access_token = create_access_token(identity=user.public_id, additional_claims=claims)

            user_data = {
                "public_id": user.public_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "roles": roles,
                "status": user.status
            }

            return jsonify(message='Login Successful', access_token=access_token, user_data=user_data)
        else:
            return jsonify(message='Incorrect credentials'), 401
    except DoesNotExist as e:
        return jsonify({'error': e.message})



# Logout route
@auth.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logs out a user by adding their token to revoked tokens
    :return: 200 logout success OR 400 error
    """
    try:
        jti = get_jwt()["jti"]
        issued_at = datetime.fromtimestamp(get_jwt()["iat"], tz=timezone.utc)  # Convert iat to datetime in utc timezone (local time by default)
        RevokedToken.revoke_token(jti=jti, issued_at=issued_at, expired_at=datetime.utcnow())
        return jsonify({"message": "Logout successful"}), 200
    except BadRequest as e:
        return jsonify({'error': str(e)}), e.code


@auth.route('/register', methods=['POST'])
def register():
    """
    process a user registration for an acount to be added as a pending registration
    :return: 200 registration success OR 400 error
    """

    if request.is_json:
        first_name = request.json['first_name']
        last_name = request.json['last_name']
        email = request.json['email']

    if not (email and first_name and last_name):
        return jsonify({"message": "Missing credentials"}), 400

    if not is_talan_email(email):
        return jsonify(message='Invalid email address'), 400

    if User.objects(email=email).first():
        return jsonify(message='Invalid email address'), 400

    try:
        RegistrationRequest.deposit_registration(first_name, last_name, email)
        return jsonify(message='registration request successful'), 200
    except BadRequest as e:
        return jsonify({'error': str(e)}), e.code


@auth.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    """
    Endpoint for password change after: a request or account creation
    :param token: itsdangerous token for verification purposes
    :return: 200 success OR 400 bad request
    """

    email = confirm_email_token(token)
    if not email:
        return jsonify({"message": "Invalid token"}), 400

    password1 = request.json["password1"]
    password2 = request.json["password2"]

    if password1 != password2:
        return jsonify({"message": "Passwords do not match"}), 400

    # Add your password strength checking logic here
    if not is_strong_password(password1):
        return jsonify({"message": "Weak password"}), 400

    user = User.objects(email=email).first()
    if user:
        user.password = generate_password_hash(password1)
        user.save()
        return jsonify({"message": "Password updated"}), 200
    else:
        return jsonify({"message": "User not found"}), 404




@auth.route('/request-password-reset', methods=['POST'])
def request_password_reset():
    """
    Sends a password reset email to the requesting user
    :param email: Email of the user requesting the password reset
    :return: 200 success response OR 400 , 404, 500
    """

    from app import app

    email = request.json['email']
    if not email:
        return jsonify({'error': 'Missing email parameter'}), 400
    try:
        user = User.objects.get(email=email)
    except DoesNotExist:
        return jsonify({'error': 'User not found'}), 404
    try:
        token = generate_email_token(email)
        #return jsonify({'token': token})

        reset_pass_url = f'{app.config["FRONTEND_WEBSITE_URL"]}/password_reset/{token}'
        html = render_template("reset.html", onboarding_url=reset_pass_url)
        subject = "You requested a password reset"
        send_email(user.email, subject, html)
        return jsonify({'message': 'password reset email sent successfully'}), 200
    except Exception as e:
        print('error sending onboarding email')
        return jsonify({'message': f'error sending email: {str(e)}'}), 500

