from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, session, current_app as app
from flask_login import current_user, login_user, logout_user
from app import db, mail, login_required
from app.main.forms import RegistrationForm, LoginForm, PasswordResetRequestForm, PasswordResetForm,ChangePasswordForm
from app.main.models import User
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message

auth_bp = Blueprint('auth', __name__)

# Before request handler to update user activity
@auth_bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        session['last_activity'] = datetime.utcnow()
        login_time = session.get('login_time')
        if login_time:
            utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
            session_duration = utc_now - login_time
            session['average_session_duration'] = session_duration.total_seconds()
            session['login_time'] = utc_now
            app.logger.debug(f"Session duration for user {current_user.username}: {session['average_session_duration']} seconds")
    else:
        app.logger.debug("Anonymous user accessing the application")
        session['last_activity'] = datetime.utcnow()

# Context processor to inject login form into templates
@auth_bp.context_processor
def inject_login_form():
    return dict(login_form=LoginForm())

# Admin dashboard route
@auth_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    total_users = User.query.count()
    return render_template('admin_dashboard.html', total_users=total_users)

@auth_bp.route('/register', methods=['POST', 'GET'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Create a new user
            user = User(
                username=form.username.data,
                email=form.email.data,
                phone=form.phone.data,
                name=form.name.data,
            )
            user.set_password(form.password.data)
            user.confirmed = True

            # Add user to the database
            db.session.add(user)
            db.session.commit()

            # Send welcome email
            send_welcome_email(user)

            # Log the user in
            login_user(user)
            app.logger.info(f"New user registered and logged in: {user.username}")

            # Flash a success message
            flash(f'Registration successful! You are now logged in as {current_user.username}.', 'success')
            return redirect(url_for('main.index'))

        except IntegrityError:
            db.session.rollback()
            app.logger.warning(f"Registration attempt failed - email already registered: {form.email.data}")
            flash('Email address is already registered. Please use Sign In.', 'danger')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error during registration: {str(e)}")
            flash('An error occurred. Please try again.', 'danger')

    return render_template('register.html', form=form)



from flask import render_template, current_app as app


def send_welcome_email(user):
    try:
        # Define the email subject
        subject = 'Welcome to Nourisha'

        # Create the email message
        msg = Message(subject=subject,
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[user.email])

        # Render the HTML template with user details
        msg.html = render_template('emails/welcome_email.html', user=user)

        # Send the email
        mail.send(msg)
        app.logger.info(f"Welcome email sent to {user.email}")

    except Exception as e:
        app.logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        # Optionally, you could handle the error further or notify someone



# User login route
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

                app.logger.info(f"User logged in: {user.username}, IP: {user.last_login_ip}")

                flash(f'Welcome back, {current_user.username}!', 'success')
                redirect_url = url_for('admin.admin_dashboard') if user.role and user.role.name == 'admin' else url_for('main.product_listing')

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': True, 'redirect': redirect_url})

                return redirect(redirect_url)

            app.logger.warning(f"Unconfirmed account login attempt: {user.username}")
            flash('Your account is not confirmed. Please check your email for the confirmation link.', 'warning')
        else:
            app.logger.warning(f"Invalid login credentials: {identifier}")
            flash('Invalid credentials. Please check your username/email/phone number and password.', 'danger')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'html': render_template('user_auth.html', login_form=login_form)})

    return render_template('user_auth.html', login_form=login_form)


# Check authentication status route (useful for AJAX requests)
@auth_bp.route('/check_authentication', methods=['GET'])
def check_authentication():
    app.logger.debug(f"Check authentication status: {current_user.is_authenticated}")
    return jsonify({'is_authenticated': current_user.is_authenticated})

# User logout route
@auth_bp.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    app.logger.info(f"User logged out: {username}")
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.product_listing'))

# Generate a password reset token
def generate_reset_token(user, expires_sec=1800):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return s.dumps(user.email, salt=app.config['SECURITY_PASSWORD_SALT'])

# Verify the password reset token
def verify_reset_token(token):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt=app.config['SECURITY_PASSWORD_SALT'], max_age=3600)
    except Exception:
        return None
    return User.query.filter_by(email=email).first()

# Send a password reset email
def send_reset_email(user):
    # Generate the password reset token
    token = generate_reset_token(user)
    
    # Create the URL for the password reset endpoint
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    # Create the email message
    msg = Message(
        subject='Password Reset Request',
        sender=app.config['MAIL_DEFAULT_SENDER'],  # Prefer using MAIL_DEFAULT_SENDER for consistency
        recipients=[user.email],
        html=f'''
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #007bff;">Password Reset Request</h2>
                <p>Hello {user.username},</p>
                <p>To reset your password, please click the button below:</p>
                <a href="{reset_url}" style="display: inline-block; padding: 12px 20px; font-size: 16px; font-weight: bold; color: #fff; background-color: #007bff; text-decoration: none; border-radius: 5px;">Reset Password</a>
                <p>If you did not request this change, please ignore this email. No changes will be made to your account.</p>
                <p>Thank you,<br>Nourisha Groceries</p>
                <footer style="margin-top: 20px; font-size: 12px; color: #777;">
                    <p>If you have any questions, feel free to <a href="mailto:support@yourdomain.com" style="color: #007bff;">contact us</a>.</p>
                </footer>
            </div>
        </body>
        </html>
        '''
    )
    
    try:
        # Send the email
        mail.send(msg)
        print("Password reset email sent successfully.")
    except Exception as e:
        # Handle exceptions during email sending
        print(f"Error sending password reset email: {e}")

# Password reset request route
@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('auth.login'))
        else:
            flash('No account with that email address exists.', 'danger')
    
    return render_template('reset_password_request.html', form=form)

# Password reset route
@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    user = verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired token', 'danger')
        return redirect(url_for('auth.reset_password_request'))

    form = PasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', form=form)

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.old_password.data):
            current_user.set_password(form.new_password.data)
            flash('Your password has been updated!')
            return redirect(url_for('main.index'))
        else:
            flash('Old password is incorrect.')
    return render_template('change_password.html', form=form)
