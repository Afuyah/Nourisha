from app import create_app, db
from app.main.models import User, Role

def create_admin_user():
    app = create_app()

    with app.app_context():
        # Create the 'admin' role if it doesn't exist
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin')
            db.session.add(admin_role)
            db.session.commit()

        # Create the admin user
        admin_user = User.query.filter_by(username='bha').first()
        if not admin_user:
            admin_user = User(
                username='bha',
                email='jhsync@gmail.com',
                phone='1044314',
                name='bha bha',
                confirmed=True,
            )
            admin_user.set_password('12x')  # Replace with a secure password
            admin_user.role = admin_role
            db.session.add(admin_user)
            db.session.commit()

if __name__ == '__main__':
    create_admin_user()
    print(' executed successfully.')
