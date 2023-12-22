from flask import Blueprint

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

def create_cart_blueprint():
    # Add any additional setup for the admin blueprint here
    return cart_bp