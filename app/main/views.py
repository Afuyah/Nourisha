from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, login_required, logout_user, current_user
from app import db
from app.main import bp
from app.admin import admin_bp
from app.main.models import User, Role
from app.main.forms import RegistrationForm, LoginForm



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
            flash('Invalid phone number or password', 'danger')
    return render_template('login.html', form=form)
