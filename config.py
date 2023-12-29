import os
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import secrets

db = SQLAlchemy()
migrate = Migrate()


class Config: 
    SECRET_KEY = secrets.token_hex(16)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///naurish_a_g_stores.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    SAFARICOM_API_KEY = 'your_api_key'
    SAFARICOM_API_SECRET = 'your_api_secret'
    SAFARICOM_LNM_PASSKEY = 'your_lnm_passkey'
    SAFARICOM_SHORTCODE = 'your_shortcode'
    SAFARICOM_LNM_CALLBACK_URL = 'your_callback_url'
  
