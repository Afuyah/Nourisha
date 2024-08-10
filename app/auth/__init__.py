from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def create_cart_blueprint():
    # Add any additional setup for the admin blueprint here
    return auth_bp
    