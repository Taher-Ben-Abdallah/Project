from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from werkzeug.exceptions import InternalServerError, BadRequest

from app.tools.nmap_scanner import run_nmap_scan, host_discovery

# Define blueprints
nmap = Blueprint('nmap', __name__)


@nmap.route('/run_scan', methods=['POST'], endpoint='nmap_scan')
@jwt_required
def run_scan():
    """

    :return:
    """

    try:
        data = request.json

        # Validate the input
        if 'targets' not in data:
            raise BadRequest('Missing "targets" field in input data')

        # Extract input parameters
        targets = data.get('targets')
        scan_type = data.get('scan_type', None)
        options = data.get('options', None)
        ports = data.get('ports', None)
        scripts = data.get('scripts', None)

        # Run the Nmap scan
        scan_results = run_nmap_scan(targets, scan_type, options, ports, scripts)

        return jsonify({"results": scan_results}), 200
    except KeyError:
        return jsonify(error="Missing or incorrect fields"), 400
    except BadRequest as e:
        return jsonify({"error": str(e)}), e.code
    except Exception as e:
        return jsonify({"error": "An internal server error occurred"}), 500


@nmap.route('/discover-hosts', methods=['POST'])
@jwt_required
def discover_hosts():
    try:
        subnet = request.json.get('subnet')

        # Perform host discovery using the host_discovery function
        discovered_hosts = host_discovery(subnet)

        return jsonify({"discovered_hosts": discovered_hosts}), 200

    except KeyError as e:
        return jsonify({"error": "Missing 'subnet' field in request data"}), 400
    except InternalServerError as e:
        return jsonify({"error": "Unable to run host discovery"}), e.code
    except Exception as e:
        return jsonify({"error": "An internal server error occurred"}), 500
