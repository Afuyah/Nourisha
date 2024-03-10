# Import necessary modules and classes
from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import current_user, login_required
from app.main.models import User, Location, Order, OrderItem
from app.main.models import Cart, Product, Location, Order, Arealine, NearestPlace, UserDeliveryInfo
from app.cart import cart_bp
from app.main.forms import CheckoutForm, AddProductForm
from app import db, mail
from flask_mail import Message
from app.main import bp
from functools import wraps

# Decorator for login-required routes
def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please Login to complete this action!.', 'warning')
            return redirect(url_for('main.login', next=request.url))
        return func(*args, **kwargs)

    return decorated_function

# Route to add a product to the cart
@cart_bp.route('/add_to_cart/<int:product_id>/<int:quantity>', methods=['POST'])
@login_required
def add_to_cart(product_id, quantity):
    product = Product.query.get_or_404(product_id)

    if quantity <= 0:
        flash('Quantity must be greater than zero.', 'danger')
        return redirect(url_for('main.product_details', product_id=product.id))

    if quantity > product.quantity_in_stock:
        flash(
            'Sorry, but we have only {} items available in stock.'.format(
                product.quantity_in_stock), 'danger')
        return redirect(url_for('main.product_details', product_id=product.id))

    cart_item = Cart.query.filter_by(user_id=current_user.id,
                                      product_id=product.id).first()
    quantity = int(request.form.get('quantity'))
    custom_description = request.form.get('custom_description', '')

    if cart_item:
        cart_item.quantity += quantity
        cart_item.custom_description = custom_description
    else:
        cart_item = Cart(user_id=current_user.id,
                          product_id=product.id,
                          quantity=quantity,
                          custom_description=custom_description)
        db.session.add(cart_item)

    product.quantity_in_stock -= quantity

    try:
        db.session.commit()
        flash('Item added to cart successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding item to cart: {str(e)}', 'danger')

    return redirect(url_for('main.product_listing', product_id=product.id))

# Route to view the cart
@cart_bp.route('/view_cart')
@login_required
def view_cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    product = None
    if cart_items:
        product = cart_items[0].product

    total_price = sum(item.product.unit_price * item.quantity
                      for item in cart_items)

    form = AddProductForm()  # Replace with the actual form you're using

    return render_template('view_cart.html',
                           cart_items=cart_items,
                           total_price=total_price,
                           form=form)

# Function to calculate the total amount in the cart
def calculate_total_amount():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total_amount = 0
    for cart_item in cart_items:
        total_amount += cart_item.product.unit_price * cart_item.quantity
    total_amount += 200  # Add shipping fee
    return total_amount

# Route to get the cart count as JSON
@cart_bp.route('/get_cart_count', methods=['GET'])
@login_required
def get_cart_count():
    try:
        cart_count = Cart.query.filter_by(user_id=current_user.id).count()
        return jsonify({'status': 'success', 'cart_count': cart_count})
    except Exception as e:
        current_app.logger.error('Error fetching cart count: %s', str(e))
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500

# Route to get product quantity as JSON
@cart_bp.route('/api/get_quantity/<int:product_id>', methods=['GET'])
@login_required
def get_product_quantity(product_id):
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        quantity = cart_item.quantity
        return jsonify({'status': 'success', 'data': {'quantity': quantity}})
    else:
        return jsonify({'status': 'success', 'data': {'quantity': 0}})

# Route to update the cart (increment/decrement quantity)
@bp.route('/cart/api/update', methods=['POST'])
def update_cart():
    try:
        data = request.get_json()
        product_id = data.get('productId')
        action = data.get('action')

        user_id = get_authenticated_user_id()

        if user_id is None:
            raise ValueError('User not authenticated')

        update_cart_in_database(user_id, product_id, action)

        updated_cart_info = get_updated_cart_info(user_id)

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
        current_app.logger.error('Error updating cart: %s', str(e))
        response_data = {
            'status': 'error',
            'message': 'Internal Server Error: ' + str(e),
        }
        return jsonify(response_data), 500

# Function to get updated cart info
def get_updated_cart_info(user_id):
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    total_price = sum(cart_item.product.unit_price * cart_item.quantity
                      for cart_item in cart_items)

    return {
        'cartItems': [{
            'productId': item.product_id,
            'quantity': item.quantity,
            'subtotal': item.product.unit_price * item.quantity
        } for item in cart_items],
        'totalPrice': total_price,
    }

# Function to update the cart in the database
def update_cart_in_database(user_id, product_id, action):
    cart_item = Cart.query.filter_by(user_id=user_id,
                                   product_id=product_id).first()

    if cart_item:
        if action == 'increment':
            cart_item.quantity += 1
        elif action == 'decrement' and cart_item.quantity > 1:
            cart_item.quantity -= 1
    else:
        cart_item = Cart(user_id=user_id, product_id=product_id, quantity=1)
        db.session.add(cart_item)

    product = Product.query.get(product_id)
    if product:
        if action == 'increment' and product.quantity_in_stock > 0:
            product.quantity_in_stock -= 1
        elif action == 'decrement':
            product.quantity_in_stock += 1

    db.session.commit()

# Function to get authenticated user's ID
def get_authenticated_user_id():
    return current_user.get_id()

# Route to clear the cart
@bp.route('/main/cart/clear_cart', methods=['POST'])
def clear_cart():
    try:
        user_id = get_authenticated_user_id()

        if user_id is None:
            raise ValueError('User not authenticated')

        cart_items = Cart.query.filter_by(user_id=user_id).all()

        for cart_item in cart_items:
            product = cart_item.product
            product.quantity_in_stock += cart_item.quantity

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

# Function to clear the cart in the database
def clear_cart_in_database(user_id):
    Cart.query.filter_by(user_id=user_id).delete()
    db.session.commit()

# Route to check product quantity in stock as JSON
@cart_bp.route('/main/api/_in_stock/<int:product_id>',
               methods=['GET'])
def _in_stock(product_id):
    try:
        product = Product.query.get(product_id)

        if not product:
            response_data = {
                'status': 'error',
                'message': 'Product not found',
            }
            return jsonify(response_data), 404

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

    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    total_price = sum(cart_item.product.unit_price * cart_item.quantity
                      for cart_item in cart_items)

    custom_description = cart_items[0].custom_description if cart_items else None

    locations = Location.query.all()
    form.location.choices = [(location.id, location.name) for location in locations]

    arealines = Arealine.query.all()
    form.arealine.choices = [(arealine.id, arealine.name) for arealine in arealines]

    nearest_places = NearestPlace.query.all()
    form.nearest_place.choices = [(place.id, place.name) for place in nearest_places]

    if form.validate_on_submit():
        if form.use_saved_address.data:
            # User has opted to use saved address
            delivery_info = current_user.delivery_info.first()
            if delivery_info:
                form.location.data = delivery_info.location_id
                form.arealine.data = delivery_info.arealine_id
                form.nearest_place.data = delivery_info.nearest_place_id
                form.address_line.data = delivery_info.address_line
                form.additional_info.data = delivery_info.additional_info
            else:
                flash('No saved delivery information found.', 'warning')
        else:
            # User is entering a new address, save it
            delivery_info = UserDeliveryInfo(
                user_id=current_user.id,
                location_id=form.location.data,
                arealine_id=form.arealine.data,
                nearest_place_id=form.nearest_place.data,
                address_line=form.address_line.data,
                additional_info=form.additional_info.data
            )
            db.session.add(delivery_info)
            db.session.commit()

        order = Order(
            user_id=current_user.id,
            status='pending',
            total_price=total_price,
            location_id=form.location.data,
            arealine_id=form.arealine.data,
            nearest_place_id=form.nearest_place.data,
            address_line=form.address_line.data,
            additional_info=form.additional_info.data,
            payment_method=form.payment_method.data,
            custom_description=custom_description
        )

        for cart_item in cart_items:
            order_item = OrderItem(
                order=order,
                product_id=cart_item.product.id,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.unit_price,
                custom_description=cart_item.custom_description
            )
            db.session.add(order_item)

        db.session.add(order)
        db.session.commit()

        order.update_order_day_of_week()

        Cart.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        transaction_id = order.id

        send_order_confirmation_email(current_user.email, 'afuyaah@gmail.com', order)

        flash('Order placed successfully! Redirecting to the payment page...', 'success')
        return redirect(url_for('payments.mpesa_payment', order_id=order.id))

    return render_template('checkout.html', form=form, cart_items=cart_items, total_price=total_price)





# Function to send order confirmation emails
def  send_order_confirmation_email(user_email, admin_email, order):
    user_subject = 'Order Confirmation - Your Order was Successful'
    user_body = f'Thank you for your order!\n\nOrder ID: {order.id}\nTotal Price: {order.total_price}\n\nWe will process your order shortly.'
    user_msg = Message(user_subject, recipients=[user_email], body=user_body)
    mail.send(user_msg)

    admin_subject = 'New Order Alert'
    admin_body = f'New order received!\n\nOrder ID: {order.id}\nUser: {order.user.username}\nTotal Price: {order.total_price}'
    admin_msg = Message(admin_subject, recipients=[admin_email], body=admin_body)
    mail.send(admin_msg)

# Route to remove item from the cart
@cart_bp.route('/api/remove', methods=['POST'])
@login_required
def remove_from_cart():
    try:
        data = request.get_json()
        product_id = data.get('productId')

        user_id = get_authenticated_user_id()

        if user_id is None:
            raise ValueError('User not authenticated')

        remove_item_from_cart(user_id, product_id)

        updated_cart_info = get_updated_cart_info(user_id)

        response_data = {
            'status': 'success',
            'message': 'Item removed from cart successfully',
            'data': {
                'cartItems': updated_cart_info['cartItems'],
                'totalPrice': updated_cart_info['totalPrice'],
            }
        }

        return jsonify(response_data)

    except Exception as e:
        current_app.logger.error('Error removing item from cart: %s', str(e))

        response_data = {
            'status': 'error',
            'message': 'Internal Server Error: ' + str(e),
        }
        return jsonify(response_data), 500

# Function to remove item from the cart in the database
def remove_item_from_cart(user_id, product_id):
    cart_item = Cart.query.filter_by(user_id=user_id,
                                   product_id=product_id).first()

    if cart_item:
        product = Product.query.get(product_id)
        if product:
            product.quantity_in_stock += cart_item.quantity

        db.session.delete(cart_item)
        db.session.commit()
