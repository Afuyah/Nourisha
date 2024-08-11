from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, session, current_app as app
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.main.forms import RegistrationForm, LoginForm
from app.main.models import User
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint('auth', __name__)

@auth_bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

    login_time = session.get('login_time')

    if login_time:
        utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        session_duration = utc_now - login_time
        session['average_session_duration'] = session_duration.total_seconds()
        session['login_time'] = utc_now


@auth_bp.route('/register', methods=['POST', 'GET'])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            # Create a new user instance
            user = User(
                username=form.username.data,
                email=form.email.data,
                phone=form.phone.data,
                name=form.name.data,
            )

            # Set the user password
            user.set_password(form.password.data)

            # Set confirmed to True to allow immediate login
            user.confirmed = True

            # Add the user to the database
            db.session.add(user)
            db.session.commit()

            # Automatically log in the user after registration
            login_user(user)

            flash(f'Registration successful! You are now logged in as {current_user.username}.', 'success')
            return redirect(url_for('main.index'))

        except IntegrityError:
            db.session.rollback()
            flash('Email address is already registered. Please use Sign In.', 'danger')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error during registration: {str(e)}')
            flash('An error occurred. Please try again.', 'danger')

    return render_template('register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()

    if login_form.validate_on_submit():
        identifier = login_form.identifier.data
        password = login_form.password.data

        user = User.query.filter(
            (User.email == identifier) | 
            (User.phone == identifier) | 
            (User.username == identifier)
        ).first()

        if user and user.check_password(password):
            if user.confirmed:
                login_user(user)
                session['login_time'] = datetime.utcnow()
                user.last_login_date = datetime.utcnow()
                user.last_login_ip = request.remote_addr
                db.session.commit()

                flash(f'Welcome back, {current_user.username}!', 'success')

                redirect_url = url_for('admin.admin_dashboard') if user.role and user.role.name == 'admin' else url_for('main.product_listing')

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': True, 'redirect': redirect_url})

                return redirect(redirect_url)

            flash('Your account is not confirmed. Please check your email for the confirmation link.', 'warning')
        else:
            flash('Invalid credentials. Please check your username/email/phone number and password.', 'danger')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'html': render_template('user_auth.html', login_form=login_form)})

    return render_template('user_auth.html', login_form=login_form)

@auth_bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

    login_time = session.get('login_time')

    if login_time:
        utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        session_duration = utc_now - login_time
        session['average_session_duration'] = session_duration.total_seconds()
        session['login_time'] = utc_now

@auth_bp.route('/check_authentication', methods=['GET'])
def check_authentication():
    return jsonify({'is_authenticated': current_user.is_authenticated})

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.product_listing'))




