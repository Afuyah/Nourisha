from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from app import create_app,db 

# Create the Flask app within the application context
app = create_app()
app.config['STATIC_URL_PATH'] = '/static'
# Initialize the database
with app.app_context():
    db.create_all()
    
if __name__ == '__main__':
    app.run()
