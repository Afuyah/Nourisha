from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
csrf = CSRFProtect(app)

from app import routes

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=81)

    # Create the database tables
    with app.app_context():
        db.create_all()