from flask import Blueprint, jsonify, request

from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from mongoengine import ValidationError
from werkzeug.exceptions import Forbidden, BadRequest, NotFound, abort, InternalServerError

from app.models.user import Role
from app.models.user import User

from .middleware import admin_required, team_leader_required
from app.models.mission import Mission

# Define blueprints
missions = Blueprint('missions', __name__)

'''
IF ADMIN => GET ALL MISSIONS
ELSE => GET MY MISSIONS
'''


@missions.route('/<string:mission_id>', methods=['GET'])
@jwt_required()
def get_mission(mission_id):
    """

    :param mission_id:
    :return:
    """

    token_public_id = get_jwt_identity()
    try:
        # Check that the "admin" role is present in the list of roles
        claims = get_jwt()['claims']
        roles = claims['roles']
        if Role.ADMIN.value in roles:
            if any(role != Role.ADMIN.value for role in roles):
                return {'message': 'Invalid token (roles)'}, 400

            mission_data = Mission.get_mission()
        else:
            mission_data = Mission.get_mission(member_id=token_public_id)
    except KeyError:
        return jsonify(message="Invalid token"), 401
    except InternalServerError as e:
        return jsonify(message="Something went wrong"), e.code

    return jsonify(mission_data=mission_data), 200


@missions.route('/', methods=['GET'])
@jwt_required()
def get_missions():
    """

    :return:
    """

    token_public_id = get_jwt_identity()
    try:
        # Check that the "admin" role is present in the list of roles
        claims = get_jwt()['claims']
        roles = claims['roles']
        if Role.ADMIN.value in roles:
            if any(role != Role.ADMIN.value for role in roles):
                return {'message': 'Invalid token (roles)'}, 400

            missions_list = Mission.get_missions_overview()
        else:
            missions_list = Mission.get_missions_overview(member_id=token_public_id)
    except KeyError:
        return jsonify(message="Invalid token"), 401
    except InternalServerError as e:
        return jsonify(message="Something went wrong"), e.code
    except Forbidden as e:  # raised in get_missions_overview()
        return jsonify(message="Unauthorized operation"), e.code

    return jsonify(missions_list=missions_list), 200


# TL required

@missions.route('/add', methods=['POST'])
@team_leader_required
@jwt_required()
def add_mission():
    """

    :return:
    """

    team_leader = get_jwt_identity()
    data = request.get_json()
    if not data['team_leader']:
        data['team_leader'] = team_leader
    if data is None:
        return jsonify(error="missing information"), 400

    try:
        mission_data = Mission.create_mission(data)
    except BadRequest as e:
        return jsonify(error=str(e)), e.code
    except InternalServerError as e:
        return jsonify(error="something went wrong"), e.code

    return jsonify(message="mission created successfully", mission=mission_data), 200


@missions.route('/<string:mission_id>/assign_members', methods=['PUT'])
@team_leader_required
@jwt_required()
def assign_members(mission_id):
    """

    :param mission_id:
    :return:
    """
    try:
        members = request.json["members"]
        if not (members and isinstance(members, list)):
            raise BadRequest
        Mission.update_team(mission_id, members, assign=True)  # use either assign and remove variables with update_team
    except (KeyError, BadRequest):
        return jsonify(message="Bad request"), BadRequest.code
    except InternalServerError as e:
        return jsonify(message="Something went wrong"), e.code
    except NotFound as e:
        return jsonify(message={str(e)}), e.code

    return jsonify({'message': 'members assigned successfully'}), 200


@missions.route('/<string:mission_id>/assign_members', methods=['PUT'])
@team_leader_required
@jwt_required()
def remove_members(mission_id):
    """

    :param mission_id:
    :return:
    """
    try:
        members = request.json["members"]
        if not (members and isinstance(members, list)):
            raise BadRequest
        Mission.update_team(mission_id, members, remove=True)  # use either assign and remove variables with update_team
    except (KeyError, BadRequest):
        return jsonify(message="Bad request"), BadRequest.code
    except InternalServerError as e:
        return jsonify(message="Something went wrong"), e.code
    except NotFound as e:
        return jsonify(message={str(e)}), e.code

    return jsonify({'message': 'members removed successfully'}), 200


@missions.route('/<string:mission_id>/delete', methods=['DELETE'])
@team_leader_required
@jwt_required()
def delete_mission(mission_id):
    """

    :param mission_id:
    :return:
    """
    try:
        Mission.delete_mission(mission_id)
    except NotFound as e:
        return jsonify(message="Mission not found"), e.code

    return jsonify({'message': 'mission deleted successfully'}), 200
