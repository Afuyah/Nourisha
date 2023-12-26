from flask_mail import Message
from flask import url_for
from app import mail

def send_confirmation_email(user):
    confirm_url = url_for('main.confirm', token=user.confirmation_token, _external=True)
    subject = 'Confirm Your Account'
    recipients = [user.email]
    
    # You can customize the email content using HTML templates
    html_body = f"""
    <p>Dear {user.username},</p>
    <p>Thank you for Joining Naurisha Family. Please click the following link to confirm your account:</p>
    <p><a href="{confirm_url}">Confirm Account</a></p>
    <p>Thank you!</p>
    """

    msg = Message(subject, recipients=recipients)
    msg.html = html_body

    mail.send(msg)