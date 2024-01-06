from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from app import create_app, db
from flask_migrate import Migrate

# Initialize Flask application instance
app = create_app()
migrate = Migrate(app, db)

# Initialize the database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81, debug=True)
