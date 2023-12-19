from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, validators

class RegistrationForm(FlaskForm):
    username = StringField('Username', [validators.InputRequired()], label='Your Username')
    password = PasswordField('Password', [validators.InputRequired(), validators.EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField('Confirm Password')
    email = StringField('Email', [validators.InputRequired(), validators.Email(message='Enter a valid email address.')])
    role = SelectField('Role', choices=[('user', 'User'), ('delivery', 'Delivery Personnel'), ('admin', 'Admin')], default='user')
    first_name = StringField('First Name')
    last_name = StringField('Last Name')
    phone_number = StringField('Phone Number')
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email_or_phone = StringField('Email or Phone Number', [validators.InputRequired()])
    password = PasswordField('Password', [validators.InputRequired(), validators.Length(min=6)])
    submit = SubmitField('Login')
