from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from app import create_app,db 

# Create the Flask app within the application context
application = create_app()
application.config['STATIC_URL_PATH'] = '/static'
# Initialize the database
with application.app_context():
    db.create_all()
    
if __name__ == '__main__':
    application.run(host='0.0.0.0', port=81, 
            debug=True)
