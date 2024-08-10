from flask import Blueprint

role_bp = Blueprint('role', __name__, url_prefix='/role')

def create_role_blueprint():
  
    return role_bp