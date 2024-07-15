from flask import Blueprint

site_bp = Blueprint('site', __name__, url_prefix='/site')

def create_site_blueprint():
   
    return site_bp