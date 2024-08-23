from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from app import db, socketio, admin_required
from app.main.models import Message
from flask_wtf.csrf import CSRFError
from app.messages import message_bp


@message_bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.json
    sender_id = current_user.id
    receiver_id = data.get('receiver_id')
    message_text = data.get('message_text')

    if not receiver_id or not message_text:
        return jsonify({'error': 'Missing required fields'}), 400

    message = Message(sender_id=sender_id, receiver_id=receiver_id, message_text=message_text)
    db.session.add(message)
    db.session.commit()

    # Emit the message to the receiver in real-time
    socketio.emit('new_message', message.to_dict(), room=f"user_{receiver_id}")

    return jsonify({'status': 'Message sent'})

@message_bp.route('/get_messages', methods=['GET'])
@login_required
def get_messages():
    user_id = current_user.id

    received_messages = Message.query.filter_by(receiver_id=user_id).all()
    sent_messages = Message.query.filter_by(sender_id=user_id).all()

    messages = {
        'received': [msg.to_dict() for msg in received_messages],
        'sent': [msg.to_dict() for msg in sent_messages]
    }

    return jsonify(messages)


@message_bp.route('/chat')
@login_required
def chat_interface():
    return render_template('chat/message.html')

@message_bp.route('/admin_chat', methods=['GET', 'POST'])
@login_required
@admin_required  # Ensure only admins can access
def admin_chat_interface():
    if request.method == 'POST':
        message_id = request.form.get('message_id')
        response_text = request.form.get('response_text')

        if message_id and response_text:
            message = Message.query.get(message_id)
            if message:
                reply_message = Message(sender_id=current_user.id, receiver_id=message.sender_id, message_text=response_text)
                db.session.add(reply_message)
                message.status = 'read'
                message.read_timestamp = datetime.utcnow()  # Update the read timestamp
                db.session.commit()
                flash('Reply sent successfully!', 'success')
                return redirect(url_for('messages.admin_chat'))

    # Get unread messages for the admin and mark them as read
    messages = Message.query.filter_by(receiver_id=current_user.id, status='unread').all()
    for message in messages:
        message.status = 'read'
        message.read_timestamp = datetime.utcnow()
    db.session.commit()

    return render_template('chat/admin_chat.html', messages=messages)


@message_bp.errorhandler(CSRFError)
def handle_csrf_error(e):
    return jsonify({'error': 'CSRF token missing or invalid'}), 400
