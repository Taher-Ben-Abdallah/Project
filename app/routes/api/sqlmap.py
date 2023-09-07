
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from werkzeug.exceptions import InternalServerError, BadRequest

from app.tools.nmap_scanner import run_nmap_scan, host_discovery
from app.tools.sqlmap import run_tables_dump

# Define blueprints
sqlmap = Blueprint('nmap', __name__)


@sqlmap.route('/dump_tables', methods=['POST'])
@jwt_required
def dump_tables():

    try:
        target = request.json['target']
        options = request.json['options']

        results = run_tables_dump(target=target, options=options)

    except KeyError:
        return jsonify(error="Invalid input"), 400
    except InternalServerError as e:
        return jsonify(error=f"Internal Server Error: {e.message}"), e.code

    return jsonify(result="result"), 200
