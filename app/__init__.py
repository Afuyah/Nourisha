from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from flask_wtf.csrf import CSRFProtect

from datetime import timedelta
from flask_mail import Mail



db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()


def create_app():
    app = Flask(__name__)
  
    app.config['SECRET_KEY'] = 'mysecretkey'
    app.config.from_object(Config)
    mail.init_app(app)
   # Email configuration
    #app.config['MAIL_SERVER'] = 'smtp.live.com'
   # app.config['MAIL_PORT'] = 587  # or your mail server's port
   #app.config['MAIL_USE_TLS'] = True
    #app.config['MAIL_USE_SSL'] = False
    #app.config['MAIL_USERNAME'] = 'henryafuya@hotmail.com'
    #app.config['MAIL_PASSWORD'] = 'H3nr1X@54'
    #app.config['MAIL_DEFAULT_SENDER'] = 'henryafuya@hotmail.com'
    #app.config['MAIL_DEBUG'] = True
    app.config['MAIL_SERVER']='sandbox.smtp.mailtrap.io'
    app.config['MAIL_PORT'] = 2525
    app.config['MAIL_USERNAME'] = '1ad3be1d9fa9c4'
    app.config['MAIL_PASSWORD'] = '6d4968f39bca9e'
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False


# Create the Mail object
   

  
      
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

    from app.payments.routes import payment_bp
    app.register_blueprint(payment_bp)
   
    from app.cart.routes import cart_bp
    app.register_blueprint(cart_bp)
 # Add other blueprints and configurations as needed

# User loader function
    from app.main.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    
    return app
