from flask import render_template, abort, Blueprint,flash, redirect, url_for, request, jsonify, send_file, session,current_app
from flask_login import current_user, login_user, logout_user, login_required
from app.payments import payment_bp
from app.main.models import Order
# Route for handling M-Pesa payment
@payment_bp.route('/mpesa_payment/<int:order_id>', methods=['GET'])
@login_required
def mpesa_payment(order_id):
    # Fetch the order from the database
    order = Order.query.get_or_404(order_id)

    # Ensure that the current user is the owner of the order
    if order.user_id != current_user.id:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))

    # Render the payment page with order details
    return render_template('mpesa_payment.html', order=order)


@payment_bp.route('/mpesa_callback', methods=['POST'])
def mpesa_callback():
    # Extract the relevant information from the M-Pesa callback
    mpesa_data = request.get_json()

    # Extract relevant payment details
    transaction_id = mpesa_data.get('transaction_id')
    payment_status = mpesa_data.get('payment_status')
    amount_paid = mpesa_data.get('amount_paid')
    order_id = mpesa_data.get('order_id')  # Include the order_id in the callback

    # Process the payment and update your database accordingly
    order = Order.query.get(order_id)

    if order:
        # Check if the payment status is 'completed' or 'success'
        if payment_status.lower() in ['completed', 'success']:
            # Update the payment status for the corresponding order
            order.payment_status = 'paid'
            order.payment_date = datetime.utcnow()
            order.transaction_id = transaction_id
            # Update other payment-related details
            # ...

            # Commit the changes to the database
            db.session.commit()

            # Send a response to the M-Pesa API (response might depend on M-Pesa API requirements)
            return {'status': 'success', 'message': 'Payment processed successfully'}, 200
        else:
            # Handle other payment statuses as needed
            return {'status': 'error', 'message': 'Payment status not recognized'}, 400
    else:
        # Handle the case where the order with the given order_id is not found
        return {'status': 'error', 'message': 'Order not found'}, 404
