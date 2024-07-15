from flask import Blueprint

payment_bp = Blueprint('payments', __name__, url_prefix='/payment')

def create_payment_blueprint():
  
    return payment_bp