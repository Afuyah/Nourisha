from app import db
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app.main import bp
from app.main.forms import RegistrationForm, LoginForm, AddRoleForm
from app.main.models import User, Role
from datetime import datetime
from sqlalchemy.exc import IntegrityError

@bp.route('/')
def index():
    return render_template('home.html', title='Home')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                phone=form.phone.data,
                name=form.name.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()

            flash('Registration successful!', 'success')
            return redirect(url_for('main.login'))

        except IntegrityError as e:
            db.session.rollback()
            flash('Email address is already registered. Please use Sign In.', 'danger')
            return redirect(url_for('main.register'))

    return render_template('register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Use email for login instead of phone number
        user = User.query.filter_by(phone=form.phone.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user)
            user.last_login_date = datetime.utcnow()
            user.last_login_ip = request.remote_addr
            db.session.commit()
            flash('Login successful!', 'success')

            # Redirect to the admin dashboard if the user has the 'admin' role
            if user.role and user.role.name == 'admin':
                return redirect(url_for('admin.admin_dashboard'))

            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html', form=form)

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
        role = Role(name=form.name.data)
        db.session.add(role)
        db.session.commit()
        flash('Role added successfully!', 'success')
        return redirect(url_for('main.add_role'))

    roles = Role.query.all()

    return render_template('add_role.html', form=form, roles=roles)
