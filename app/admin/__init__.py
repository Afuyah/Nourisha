from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def create_admin_blueprint():
    # Add any additional setup for the admin blueprint here
    return admin_bp