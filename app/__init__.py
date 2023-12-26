from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from datetime import timedelta
from flask_mail import Mail
import secrets


db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secrets.token_hex(16)
    app.config.from_object(Config)
    mail.init_app(app)
   # Email configuration
  
  
      
    db.init_app(app)
    login_manager.init_app(app)
    
  
    csrf = CSRFProtect(app)  # Move the initialization here
    app.config['WTF_CSRF_TIME_LIMIT'] = None
  
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.admin.routes import admin_bp
    app.register_blueprint(admin_bp)
#user Blueprint registration
    from app.user.routes import user_bp
    app.register_blueprint(user_bp)
   
    from app.cart.routes import cart_bp
    app.register_blueprint(cart_bp)
 # Add other blueprints and configurations as needed

# User loader function
    from app.main.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    migrate = Migrate(app, db)
    
    return app

