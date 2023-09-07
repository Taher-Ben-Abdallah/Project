from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

# Define blueprints
metasploit = Blueprint('metasploit', __name__)


@metasploit.route('/metasploit_function', methods=['POST'])
@jwt_required
def function():
    return jsonify(message="metasploit endpoint"), 200
