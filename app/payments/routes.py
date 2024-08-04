from flask import render_template, abort, Blueprint, flash, redirect, url_for, request, jsonify, session, current_app
from flask_login import current_user, login_required
from app.payments import payment_bp
from app.main.models import Order, Payment
from app.main.forms import CheckoutForm, PaymentForm
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

# Route to display and filter orders for admin payment update
@payment_bp.route('/admin_payments', methods=['GET', 'POST'])
@login_required
def admin_payments():
    if current_user.role.name != 'admin':
        flash('Unauthorized access!', 'error')
        return redirect(url_for('main.index'))

    form = PaymentForm()
    filter_status = request.args.get('status', 'unpaid_partially_paid')
    
    if filter_status == 'all':
        orders = Order.query
    else:
        orders = Order.query.filter(Order.payment_status.in_(['unpaid', 'partially paid']))

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        order_id = request.form.get('order_id')
        order_date = request.form.get('order_date')

        if user_id:
            orders = orders.filter_by(user_id=user_id)
        if order_id:
            orders = orders.filter_by(id=order_id)
        if order_date:
            orders = orders.filter(Order.order_date.like(f"{order_date}%"))

    orders = orders.all()
    return render_template('admin_payments.html', orders=orders, form=form, filter_status=filter_status)


# Route to update payment details manually
@payment_bp.route('/update_payment/<int:order_id>', methods=['POST'])
@login_required
def update_payment(order_id):
    if current_user.role.name != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized access!'}), 403

    order = Order.query.get_or_404(order_id)
    user = order.user

    transaction_id = request.form.get('transaction_id')
    try:
        amount_paid = float(request.form.get('amount_paid'))
        payment_date = request.form.get('payment_date')
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Invalid data format.'}), 400

    if not all([transaction_id, amount_paid, payment_date]):
        return jsonify({'status': 'error', 'message': 'All payment fields are required.'}), 400

    try:
        payment_date = datetime.fromisoformat(payment_date)

        payment = Payment(
            order_id=order.id,
            transaction_id=transaction_id,
            amount_paid=amount_paid,
            payment_date=payment_date
        )
        db.session.add(payment)

        # Calculate total due and paid amounts for the user
        total_user_orders = Order.query.filter(Order.user_id == user.id, Order.status != 'cancelled').all()
        total_amount_due = sum(o.total_price for o in total_user_orders)
        total_amount_paid = sum(p.amount_paid for o in total_user_orders for p in o.payments)
        balance = total_amount_due - total_amount_paid

        # Update order statuses based on the balance
        for o in total_user_orders:
            if balance <= 0:
                o.payment_status = 'paid'
                if o.status == 'delivered':
                    o.status = 'completed'
            else:
                o.payment_status = 'partially paid'
                if amount_paid >= balance and o.status != 'delivered':
                    o.status = 'pending'

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Payment updated successfully.'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Error updating payment for order %s: %s', order_id, e)
        return jsonify({'status': 'error', 'message': 'Failed to update payment. Please try again.'}), 500



@payment_bp.route('/get_balance/<int:order_id>', methods=['GET'])
@login_required
def get_balance(order_id):
    order = Order.query.get_or_404(order_id)
    user = order.user

    # Calculate total balance for the user
    total_user_orders = Order.query.filter(Order.user_id == user.id, Order.status != 'cancelled').all()
    total_amount_due = sum(o.total_price for o in total_user_orders)
    total_amount_paid = sum(sum(p.amount_paid for p in o.payments) for o in total_user_orders)
    balance = total_amount_due - total_amount_paid

    return jsonify({'total_balance': balance})
