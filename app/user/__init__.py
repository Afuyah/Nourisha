from flask import Blueprint

user_bp = Blueprint('user', __name__, url_prefix='/user')

def create_cart_blueprint():
    # Add any additional setup for the admin blueprint here
    return user_bp