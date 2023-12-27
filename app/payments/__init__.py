from flask import Blueprint

payment_bp = Blueprint('payments', __name__, url_prefix='/payment')

def create_payment_blueprint():
    # Add any additional setup for the admin blueprint here
    return payment_bp