from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from app.routes.api.middleware import team_leader_required

pocs = Blueprint('pocs', __name__)


@pocs.route('')
@jwt_required()
def get_pocs():

    return jsonify(message= 'getting pocs')
