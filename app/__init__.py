# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_migrate import Migrate
from config import Config
from datetime import timedelta
from flask_cors import CORS

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
CORS(resources={r"/*": {"origins": "*"}})

def create_app():    
    app = Flask(__name__)   
    app.config.from_object(Config)
  
    # Set the session timeout to 7 days
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['SESSION_COOKIE_NAME'] = 'myapp_session'
    app.config['SESSION_COOKIE_DURATION'] = timedelta(days=7)  # Set the cookie duration to 7 days
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    app.config['SESSION_COOKIE_SECURE'] = True

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Initialize migrate within the app context
    with app.app_context():
        migrate.init_app(app, db)

    csrf = CSRFProtect(app)
    app.config['WTF_CSRF_TIME_LIMIT'] = None

    # Blueprints registration
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.admin.routes import admin_bp
    app.register_blueprint(admin_bp)

    from app.user.routes import user_bp
    app.register_blueprint(user_bp)

    from app.payments.routes import payment_bp
    app.register_blueprint(payment_bp)

    from app.cart.routes import cart_bp
    app.register_blueprint(cart_bp)

    # User loader function
    from app.main.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
