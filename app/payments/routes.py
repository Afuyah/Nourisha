from flask import render_template, abort, Blueprint, flash, redirect, url_for, request, jsonify, session, current_app
from flask_login import current_user, login_required
from app.payments import payment_bp
from app.main.models import Order
from app.main.forms import CheckoutForm

from datetime import datetime
from app import db  

# Route for handling M-Pesa payment
@payment_bp.route('/mpesa_payment/<int:order_id>', methods=['GET'])
@login_required
def mpesa_payment(order_id):
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))
    
    form = CheckoutForm()
    return render_template('mpesa_payment.html', order=order, form=form)

# Route for M-Pesa callback
@payment_bp.route('/mpesa_callback', methods=['POST'])
def mpesa_callback():
    try:
        mpesa_data = request.get_json()

        # Log the received callback data
        current_app.logger.info('M-Pesa callback received: %s', mpesa_data)

        transaction_id = mpesa_data.get('transaction_id')
        payment_status = mpesa_data.get('payment_status')
        amount_paid = mpesa_data.get('amount_paid')
        order_id = mpesa_data.get('order_id')

        if not all([transaction_id, payment_status, amount_paid, order_id]):
            return jsonify({'status': 'error', 'message': 'Missing required parameters'}), 400

        order = Order.query.get(order_id)

        if not order:
            return jsonify({'status': 'error', 'message': 'Order not found'}), 404

        if payment_status.lower() in ['completed', 'success']:
            order.payment_status = 'paid'
            order.payment_date = datetime.utcnow()
            order.transaction_id = transaction_id

            try:
                db.session.commit()
                current_app.logger.info('Payment for order %s successfully processed.', order_id)
                return jsonify({'status': 'success', 'message': 'Payment processed successfully'}), 200
            except Exception as e:
                current_app.logger.error('Error processing payment for order %s: %s', order_id, e)
                db.session.rollback()
                return jsonify({'status': 'error', 'message': 'Failed to update order status'}), 500
        else:
            current_app.logger.warning('Unrecognized payment status for order %s: %s', order_id, payment_status)
            return jsonify({'status': 'error', 'message': 'Payment status not recognized'}), 400

    except Exception as e:
        current_app.logger.error('Error handling M-Pesa callback: %s', e)
        return jsonify({'status': 'error', 'message': 'An error occurred while processing the callback'}), 500
