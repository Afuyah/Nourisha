from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from . import app, db
from .models import User
from .forms import RegistrationForm, LoginForm
from sqlalchemy import or_
from flask_login import current_user, login_required



@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(
            username=form.username.data,
            password_hash=hashed_password,
            email=form.email.data,
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone_number=form.phone_number.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email_or_phone = form.email_or_phone.data
        password = form.password.data

        # Check if the input is an email or phone number
        user = User.query.filter(or_(User.email == email_or_phone, User.phone_number == email_or_phone)).first()

        if user and check_password_hash(user.password_hash, password):
            user.set_last_login_info()
            db.session.commit()
            flash('Login successful!')
            return redirect(url_for('dashboard', role=user.role))
        else:
            flash('Login failed. Check your email or phone number and password.')
    return render_template('login.html', form=form)
  
@app.route('/dashboard/<role>')
def dashboard(role):
    if role == 'user':
        return render_template('user_dashboard.html')
    elif role == 'delivery':
        return render_template('delivery_dashboard.html')
    elif role == 'admin':
        return render_template('admin_dashboard.html')
    else:
        flash('Invalid role!')
        return redirect(url_for('home'))

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    return render_template('user_dashboard.html', current_user=current_user)

@app.route('/admin/dashboard')
def admin_dashboard():
    # Add authentication and authorization check for admin
    return render_template('admin_dashboard.html')

@app.route('/delivery/dashboard')
def delivery_dashboard():
    # Add authentication and authorization check for delivery personnel
    return render_template('delivery_dashboard.html')