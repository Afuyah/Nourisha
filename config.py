import os
import secrets
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32)

    # SQLAlchemy Database URI
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')  # Default to SQLite for local development
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Mail Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() in ['true', '1', 'yes']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'True').lower() in ['true', '1', 'yes']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') 
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') 
    MAIL_DEBUG = os.environ.get('MAIL_DEBUG', 'False').lower() in ['true', '1', 'yes']

    # Additional Flask-Mail settings
    MAIL_MAX_EMAILS = None
    MAIL_SUPPRESS_SEND = False
    MAIL_ASCII_ATTACHMENTS = False
    MAIL_BCC = os.environ.get('MAIL_BCC')
    MAIL_CHARSET = 'utf-8'

    # Safaricom Daraja API (Add these if you are using Safaricom integration)
    SAFARICOM_API_KEY = os.environ.get('SAFARICOM_API_KEY') or 'your-api-key'
    SAFARICOM_API_SECRET = os.environ.get('SAFARICOM_API_SECRET') or 'your-api-secret'
    SAFARICOM_SHORTCODE = os.environ.get('SAFARICOM_SHORTCODE') or 'your-shortcode'
    SAFARICOM_LNM_PASSKEY = os.environ.get('SAFARICOM_LNM_PASSKEY') or 'your-lnm-passkey'
    SAFARICOM_LNM_CALLBACK_URL = os.environ.get('SAFARICOM_LNM_CALLBACK_URL') or 'https://yourdomain.com/mpesa_callback'
    SAFARICOM_ENVIRONMENT = os.environ.get('SAFARICOM_ENVIRONMENT', 'sandbox')  # Default to 'sandbox'

