import os
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import secrets



db = SQLAlchemy()
migrate = Migrate()
app = Flask(__name__)

class Config: 
    SECRET_KEY = secrets.token_hex(16)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///naurish_a_g_stores.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

