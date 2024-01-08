from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_migrate import Migrate
from config import Config
from datetime import timedelta
from flask_cors import CORS
from app import create_app, db

# Import additional models and blueprints if needed

app = create_app()
migrate = Migrate(app, db)

# Initialize the database
with app.app_context():
    db.create_all()
