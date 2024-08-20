from flask import Blueprint

product_bp = Blueprint('product', __name__, url_prefix='/product')

def create_product_blueprint():

  return product_bp
