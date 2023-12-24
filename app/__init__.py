from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from datetime import timedelta


db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SECRET_KEY'] = 'your_secret_key'
  
    db.init_app(app)
    login_manager.init_app(app)
    
  
    csrf = CSRFProtect(app)  # Move the initialization here
    app.config['WTF_CSRF_TIME_LIMIT'] = None
  
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.admin.routes import admin_bp
    app.register_blueprint(admin_bp)
   
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

