"""
Healthcheck route for the Islamic Finance API.
"""

from flask import Blueprint, jsonify
from datetime import datetime

# Create the blueprint for the healthcheck route
healthcheck_bp = Blueprint('healthcheck_bp', __name__)

@healthcheck_bp.route('', methods=['GET'])
def healthcheck():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})
