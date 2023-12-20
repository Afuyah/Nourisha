from flask import Blueprint
from flask_login import LoginManager

bp = Blueprint('main', __name__)
login_manager = LoginManager()
login_manager.login_view = 'main.login'

from app.main import routes, models, forms
