from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

# Define blueprints
zap = Blueprint('zap', __name__)

@zap.route('',methods=['POST'])
@jwt_required
def function():
    return jsonify(message="owasp zap endpoint function")
