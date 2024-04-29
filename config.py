import os
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import secrets

db = SQLAlchemy()
migrate = Migrate()




class Config:
    SECRET_KEY = secrets.token_hex(16)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False



    

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'afuya.b@gmail.com'
    MAIL_PASSWORD = 'aqjq tsee jznw aymb'
    MAIL_DEFAULT_SENDER = 'afuya.b@gmail.com'
    MAIL_DEBUG = True  # Set to False in production

    # Additional configuration for Flask-Mail
    MAIL_MAX_EMAILS = None
    MAIL_SUPPRESS_SEND = False
    MAIL_ASCII_ATTACHMENTS = False
