from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta


db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SESSION_COOKIE_SECURE'] = True

    app.config.update(
      SESSION_COOKIE_SECURE=True,
      SESSION_COOKIE_HTTPONLY=True,
      SESSION_COOKIE_SAMESITE='Lax',
      PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
      SESSION_REFRESH_EACH_REQUEST=True,
            )
  
    db.init_app(app)
    login_manager.init_app(app)

    csrf = CSRFProtect(app)  # Move the initialization here

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    from app.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin') 
    # Add other blueprints and configurations as needed

    # User loader function
    from app.main.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
