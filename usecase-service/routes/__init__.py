from flask import Blueprint
from .usecase import usecase_bp
from .healthcheck import healthcheck_bp

# Register all blueprints
def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    app.register_blueprint(usecase_bp, url_prefix='/usecase')
    app.register_blueprint(healthcheck_bp, url_prefix='/healthcheck')