from flask import Blueprint
message_bp = Blueprint('message', __name__, url_prefix='/message')

def create_mssage_blueprint():
  return message_bp
  