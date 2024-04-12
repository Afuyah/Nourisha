import os
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import secrets

db = SQLAlchemy()
migrate = Migrate()


class Config: 
    SECRET_KEY = secrets.token_hex(16)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgres://naurisha_user:62wegLsokvF6gt0sDBeY3a5EHa07h0LW@dpg-co6it2a0si5c73cgf5eg-a.oregon-postgres.render.com/naurisha'
  
#'sqlite:///naurish_a_g_stores.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    SAFARICOM_API_KEY = 'your_api_key'
    SAFARICOM_API_SECRET = 'your_api_secret'
    SAFARICOM_LNM_PASSKEY = 'your_lnm_passkey'
    SAFARICOM_SHORTCODE = 'your_shortcode'
    SAFARICOM_LNM_CALLBACK_URL = 'your_callback_url'

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
      
