from flask import Blueprint, jsonify, request, render_template

from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from mongoengine import ValidationError
from werkzeug.exceptions import Forbidden, BadRequest, NotFound, abort, InternalServerError

from app.models.user import User, Role
from app.models.registration_requests import RegistrationRequest

from .middleware import admin_required, team_leader_required, generate_email_token
from app.utils.mail import send_email

# Define blueprints
users = Blueprint('users', __name__)


@users.route('/', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
    """

    :return:
    """
    try:
        #can add filters
        #users_list = User.get_users(filters=filters)

        users_list = User.get_users()
        # Return the users_list directly
        return jsonify(users_list)
    except InternalServerError as e:
        return jsonify(message="error fetching users"), e.code



@users.route('/<public_id>', methods=['GET'])
@jwt_required()
def get_user(public_id):
    """
    Get back user information only if you are the user, or you are admin (using jwt)
    :param public_id:
    :return:
    """

    try:
        # Check if the authenticated user's public_id matches the requested public_id
        token_public_id = get_jwt_identity()
        if token_public_id != public_id:

            # Check that the "admin" role is present in the list of roles
            claims = get_jwt()['claims']
            roles = claims['roles']
            if Role.ADMIN.value not in roles:
                return {'message': 'Access denied'}, 403
            if any(role != Role.ADMIN.value for role in roles):
                return {'message': 'Invalid token (roles)'}, 400
    except KeyError:
        return jsonify(message="Invalid token"), 401

    try:
        user_data = User.get_user(public_id)
        return jsonify(user_data=user_data), 200
    except NotFound as e:
        return jsonify(message=str(e)), e.code






@users.route('/add', methods=['POST'])
@jwt_required
@admin_required
def add_user():
    """
    Adding user by admin and sending an email for onboarding
    :return:
    """
    from app import app
    try:
        email = request.json.get('email')
        first_name = request.json.get('first_name')
        last_name = request.json.get('last_name')
        roles = request.json.get('roles')

        if (Role.ADMIN.value in roles) and any(role != Role.ADMIN.value for role in roles):
            return {'message': 'used roles list not allowed'}, 400

    except KeyError:
        return jsonify({'error': 'required fields are missing'}), 400

    try:
        user = User.create_user(email, first_name, last_name, roles)
    except ValidationError as e:
        return jsonify({'message': str(e)}), 401

    try:
        # Sending email to created user to do the onboarding
        token = generate_email_token(email)

        onboarding_url = f'{app.config["FRONTEND_WEBSITE_URL"]}/onboarding/{token}'
        html = render_template("emails/onboarding.html", onboarding_url=onboarding_url)
        subject = "Bienvenue sur la plateforme !"
        send_email(user.email, subject, html)

    except Exception as e:
        print('error sending onboarding email')
        return ({'message': f'error sending onboarding email: {str(e)}'}), 500

    return jsonify({'message': f'User {first_name + last_name} created successfully.'}), 201


@users.route('/<public_id>/update', methods=['PUT'])
@admin_required
@jwt_required()
def update_user(public_id):
    """
    Update fields in user data, accepted fields are within update_data dictionary
    :param public_id:
    :return: user updated data 200 OR 404,500,400 error message
    """
    try:
        user = User.get_user(public_id)
    except NotFound:
        return jsonify({"message": "User not found"}), 404

    # Get the updated data from the JSON request or assign user data if not specified
    update_data = {
        "first_name": request.json.get("first_name", user.first_name),
        "last_name": request.json.get("last_name", user.last_name),
        "email": request.json.get("email", user.email),
        "phone": request.json.get("phone", user.phone),
    }

    # Update user's data
    try:
        updated_user = User.update_user(public_id=public_id, data=update_data)
    except (NotFound, BadRequest) as e:
        return jsonify({"message": str(e)}), e.code
    except InternalServerError as e:
        return jsonify({"message": "Something went wrong"}), e.code

    return jsonify(message="User data updated successfully", updated_user=updated_user), 200



@users.route('/<public_id>/delete', methods=['DELETE'])
@admin_required
@jwt_required()
def delete_user(public_id):
    try:
        User.delete_user(public_id)
    except NotFound as e:
        return jsonify({'error': str(e)}), e.code
    return jsonify({'message': 'User deleted'}), 200


################################################################
################### REGISTRATION HANDLING ######################

@users.route('/registration-requests/<registration_id>/accept', methods=['POST'])
@admin_required
@jwt_required()
def accept_registration(registration_id):
    """
    Accepting the pending registration requests stored in 'RegistrationRequest' collection
    and sending email to user for password setting
    :param registration_id: stored registration id
    :return: 200 (if user account made, email sent and registration deleted) OR 400, 404, 500
    """

    from app import app

    roles = request.json['roles']
    # Deny admin creation from requests
    if Role.ADMIN.value in roles:
        return jsonify({"message": "Admin role not allowed"}), 400

    try:
        reg = RegistrationRequest.get_registration_by_id(registration_id)
        User.create_user(email=reg.email, first_name=reg.first_name, last_name=reg.last_name, roles=roles)
    except BadRequest as e:
        return jsonify({'error': str(e)}), e.code

    try:
        # Sending email to created user to do the onboarding
        token = generate_email_token(reg.email)

        onboarding_url = f'{app.config["FRONTEND_WEBSITE_URL"]}/onboarding/{token}'
        html = render_template("emails/onboarding.html", onboarding_url=onboarding_url)
        subject = "Your registration request has been accepted!"
        send_email(reg.email, subject, html)
    except Exception as e:
        print('error sending onboarding email')
        return jsonify({'message': f'error sending email: {str(e)}'}), 500

    try:
        RegistrationRequest.delete_registration(registration_id)
        return jsonify({'message': 'Registration request accepted'}), 200
    except (NotFound, InternalServerError) as e:
        print(str(e))
        return jsonify({'error': 'Error deleting registration request'}), e.code


@users.route('/registration-requests/<registration_id>/reject', methods=['POST'])
@admin_required
@jwt_required()
def reject_registration(registration_id):
    """
    reject registration request by deleting it from the 'RegistrationRequest' collection
    :param registration_id:
    :return:
    """
    try:
        RegistrationRequest.delete_registration(registration_id)
        return jsonify({'message': 'Registration request deleted'}), 200
    except (NotFound, InternalServerError) as e:
        print(str(e))
        return jsonify({'error': 'Error deleting registration request'}), e.code
