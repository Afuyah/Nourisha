from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.main import bp
from app.main.forms import RegistrationForm, LoginForm
from app.main.models import User,Role, db
from datetime import datetime  # Import the datetime module
from app.main.forms import AddRoleForm

@bp.route('/')
def index():
    return render_template('/home.html', title='Home')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            phone=form.phone.data,
            name=form.name.data,
        )
        user.set_password(form.password.data)  # Set the password using the method
        db.session.add(user)
        db.session.commit()

        flash('Registration successful!', 'success')
        return redirect(url_for('main.login'))
    return render_template('/register.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(phone=form.phone.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            user.last_login_date = datetime.utcnow()
            user.last_login_ip = request.remote_addr
            db.session.commit()
            flash('Login successful!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or phone number or password', 'danger')
    return render_template('/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/add_role', methods=['GET', 'POST'])
@login_required
def add_role():
    form = AddRoleForm()

    if form.validate_on_submit():
        # Process the form data and add the role to the database
        role = Role(name=form.name.data)
        db.session.add(role)
        db.session.commit()
        flash('Role added successfully!', 'success')
        return redirect(url_for('main.add_role'))

    # Query all roles from the database
    roles = Role.query.all()

    return render_template('add_role.html', form=form, roles=roles)