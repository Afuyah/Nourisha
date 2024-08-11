from flask import Flask, session, redirect, url_for, flash, request, jsonify, current_app as app
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_migrate import Migrate
from config import Config
from datetime import timedelta
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
import os


# Extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
socketio = SocketIO()
csrf = CSRFProtect()






def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'redirect': url_for('auth.login'), 'show_modal': True})
            else:
                session['next'] = request.url
                flash('Please login to access this page.', 'warning')
                return redirect(url_for('auth.login'))
        return func(*args, **kwargs)
    return decorated_function

def admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'redirect': url_for('main.product_listing', show_modal='true')})
            else:
                session['next'] = request.url
                flash('Please login to access this page.', 'warning')
                return redirect(url_for('main.product_listing', show_modal='true'))

        if not current_user.role or current_user.role.name != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.product_listing', show_modal='true'))

        return func(*args, **kwargs)
    return decorated_function

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configuration settings
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['SESSION_COOKIE_NAME'] = 'myapp_session'
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    app.config['SESSION_COOKIE_SECURE'] = True if not app.debug else False
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' if not app.debug else 'None'

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    csrf.init_app(app)
    app.config['WTF_CSRF_TIME_LIMIT'] = None


    

    # Set up basic configuration for logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Create a file handler object
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/grocery_store.log', maxBytes=10240, backupCount=10)
    
    # Define the logging format
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    file_handler.setFormatter(formatter)
    
    # Set the log level for the file handler
    file_handler.setLevel(logging.INFO)
    
    # Add the file handler to the app's logger
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    
    # Log an application startup message
    app.logger.info('Nourisha Grocery Store application started')

    
    # Blueprints registration

    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp)
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.admin.routes import admin_bp
    app.register_blueprint(admin_bp)

    from app.role.routes import role_bp
    app.register_blueprint(role_bp)

    from app.payments.routes import payment_bp
    app.register_blueprint(payment_bp)

    from app.cart.routes import cart_bp
    app.register_blueprint(cart_bp)

    from app.site_setting.routes import site_bp
    app.register_blueprint(site_bp)

    # User loader function
    from app.main.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True, ssl_context='adhoc')
