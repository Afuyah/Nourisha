from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import current_user, login_required
from app.main.models import User, Location, Order,OrderItem
from app.main.models import Cart, Product, Location , Order
from app.cart import cart_bp
from app.main.forms import CheckoutForm, AddProductForm
from app import db, mail
from flask_mail import Message
from app.main import bp


@cart_bp.route('/add_to_cart/<int:product_id>/<int:quantity>', methods=['POST'])
@login_required
def add_to_cart(product_id, quantity):
    product = Product.query.get_or_404(product_id)

    if quantity <= 0:
        flash('Quantity must be greater than zero.', 'danger')
        return redirect(url_for('main.product_details', product_id=product.id))

    if quantity > product.quantity_in_stock:
        flash('Sorry !!! Items out of Stock.', 'danger')
        return redirect(url_for('main.product_listing', product_id=product.id))

    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product.id).first()

    if cart_item:
        # If item is already in the cart, update quantity
        cart_item.quantity += quantity
    else:
        # Otherwise, add a new item to the cart
        cart_item = Cart(user_id=current_user.id, product_id=product.id, quantity=quantity)
        db.session.add(cart_item)

    # Update stock quantity
    product.quantity_in_stock -= quantity

    db.session.commit()
    flash('Item added to cart successfully.', 'success')
    return redirect(url_for('main.product_listing', product_id=product.id))

@cart_bp.route('/view_cart')
@login_required
def view_cart():
    # Retrieve the user's cart items with product details
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    # Fetch product details for the first item in the cart
    # You might need to adjust this logic based on how you determine the product for the cart
    product = None
    if cart_items:
        product = cart_items[0].product

    # Calculate the total price for items in the cart
    total_price = sum(item.product.unit_price * item.quantity for item in cart_items)

    # Create an instance of your form
    form = AddProductForm()  # Replace with the actual form you're using

    # Render the template with the form
    return render_template('view_cart.html', cart_items=cart_items, total_price=total_price, form=form)



def calculate_total_amount():
    # Fetch user's cart items
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    # Calculate total amount
    total_amount = 0
    for cart_item in cart_items:
        total_amount += cart_item.product.unit_price * cart_item.quantity

    # Add shipping fee (200)
    total_amount += 200

    return total_amount



@bp.route('/cart/api/update', methods=['POST'])
def update_cart():
    try:
        data = request.get_json()
        product_id = data.get('productId')
        action = data.get('action')

        # Authenticate the user and obtain the user_id (replace with your actual authentication logic)
        user_id = get_authenticated_user_id()

        if user_id is None:
            raise ValueError('User not authenticated')  # You can customize this error message

        # Perform database queries to update the cart
        update_cart_in_database(user_id, product_id, action)

        # Fetch updated cart info
        updated_cart_info = get_updated_cart_info(user_id)

        # Example response
        response_data = {
            'status': 'success',
            'message': 'Cart updated successfully',
            'data': {
                'cartItems': updated_cart_info['cartItems'],
                'totalPrice': updated_cart_info['totalPrice'],
            }
        }

        return jsonify(response_data)

    except Exception as e:
        # Log the exception using the blueprint's logger
        current_app.logger.error('Error updating cart: %s', str(e))

        response_data = {
            'status': 'error',
            'message': 'Internal Server Error: ' + str(e),
        }
        return jsonify(response_data), 500

def get_updated_cart_info(user_id):
    # Perform database queries to get updated cart info
    cart_items = Cart.query.filter_by(user_id=user_id).all()

    # Calculate total price
    total_price = sum(cart_item.product.unit_price * cart_item.quantity for cart_item in cart_items)

    # Return the updated cart info
    return {
        'cartItems': [
            {'productId': item.product_id, 'quantity': item.quantity, 'subtotal': item.product.unit_price * item.quantity}
            for item in cart_items
        ],
        'totalPrice': total_price,
    }

def update_cart_in_database(user_id, product_id, action):
    # Perform database queries to update the cart
    cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

    if cart_item:
        # If the item is already in the cart, update the quantity
        if action == 'increment':
            cart_item.quantity += 1
        elif action == 'decrement' and cart_item.quantity > 1:
            cart_item.quantity -= 1
    else:
        # If the item is not in the cart, add a new item to the cart
        cart_item = Cart(user_id=user_id, product_id=product_id, quantity=1)
        db.session.add(cart_item)

    # Update quantity in stock for the corresponding product
    product = Product.query.get(product_id)
    if product:
        if action == 'increment' and product.quantity_in_stock > 0:
            product.quantity_in_stock -= 1
        elif action == 'decrement':
            product.quantity_in_stock += 1

    # Commit changes to the database
    db.session.commit()

def get_authenticated_user_id():
    # Replace this with your actual user authentication logic
    # For now, return a placeholder user_id (you should implement this based on your authentication mechanism)
    return current_user.get_id()
  
@bp.route('/main/cart/clear_cart', methods=['POST'])
def clear_cart():
    try:
        # Authenticate the user and obtain the user_id (replace with your actual authentication logic)
        user_id = get_authenticated_user_id()

        if user_id is None:
            raise ValueError('User not authenticated')  # You can customize this error message

        # Fetch cart items for the user
        cart_items = Cart.query.filter_by(user_id=user_id).all()

        # Iterate over cart items to increase quantity in stock
        for cart_item in cart_items:
            product = cart_item.product
            product.quantity_in_stock += cart_item.quantity

        # Commit changes to the database
        db.session.commit()

        clear_cart_in_database(user_id)

        response_data = {
            'status': 'success',
            'message': 'Cart cleared successfully',
        }

        return jsonify(response_data)

    except Exception as e:
        current_app.logger.error('Error clearing cart: %s', str(e))

        response_data = {
            'status': 'error',
            'message': 'Internal Server Error: ' + str(e),
        }
        return jsonify(response_data), 500

def clear_cart_in_database(user_id):
    # Clear the user's cart in the database
    Cart.query.filter_by(user_id=user_id).delete()

    # Commit changes to the database
    db.session.commit()

@cart_bp.route('/main/api/get_quantity_in_stock/<int:product_id>', methods=['GET'])
def get_quantity_in_stock(product_id):
    try:
        # Fetch the product from the database
        product = Product.query.get(product_id)

        if not product:
            response_data = {
                'status': 'error',
                'message': 'Product not found',
            }
            return jsonify(response_data), 404

        # Return the quantity in stock
        response_data = {
            'status': 'success',
            'quantity_in_stock': product.quantity_in_stock,
        }
        return jsonify(response_data)

    except Exception as e:
        current_app.logger.error('Error getting quantity in stock: %s', str(e))
        response_data = {
            'status': 'error',
            'message': 'Internal Server Error: ' + str(e),
        }
        return jsonify(response_data), 500



@cart_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    form = CheckoutForm()

    # Fetch user's cart items with product details
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    # Calculate total price
    total_price = sum(cart_item.product.unit_price * cart_item.quantity for cart_item in cart_items)

    # Set choices for the location field
    form.location.choices = [(location.id, location.location_name) for location in Location.query.all()]

    if form.validate_on_submit():
        
        # Create a new order
        order = Order(
            user_id=current_user.id,
            status='pending',  # Set status to 'pending' by default
            total_price=total_price,
            location_id=form.location.data,
            address_line=form.address_line.data,
            additional_info=form.additional_info.data,
            payment_method=form.payment_method.data
        )

        # Add order items to the order
        for cart_item in cart_items:
            order_item = OrderItem(
                order=order,
                product_id=cart_item.product.id,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.unit_price
            )
            db.session.add(order_item)

        # Commit changes to the database
        db.session.add(order)
        db.session.commit()

        # Update the day_of_week for the order
        order.update_order_day_of_week()

        # Clear the user's cart
        Cart.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        transaction_id = order.id

        # Send email alerts
        send_order_confirmation_email(current_user.email, 'afuyaah@gmail.com', order)

        # You can now redirect the user to the payment page, passing the transaction ID
        # Ensure to implement the redirection logic to the payment page
        flash('Order placed successfully! Redirecting to payment page...', 'success')
        return redirect(url_for('payments.mpesa_payment', order_id=order.id))

    return render_template('checkout.html', form=form, cart_items=cart_items, total_price=total_price)



def send_order_confirmation_email(user_email, admin_email, order):
    # Send email to the user
    user_subject = 'Order Confirmation - Your Order was Successful'
    user_body = f'Thank you for your order!\n\nOrder ID: {order.id}\nTotal Price: {order.total_price}\n\nWe will process your order shortly.'
    user_msg = Message(user_subject, recipients=[user_email], body=user_body)
    mail.send(user_msg)

    # Send email to the admin
    admin_subject = 'New Order Alert'
    admin_body = f'New order received!\n\nOrder ID: {order.id}\nUser: {order.user.username}\nTotal Price: {order.total_price}'
    admin_msg = Message(admin_subject, recipients=[admin_email], body=admin_body)
    mail.send(admin_msg)