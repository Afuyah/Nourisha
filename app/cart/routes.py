# Import necessary modules and classes
from flask import render_template, flash, redirect, url_for, request, jsonify, current_app as app, session
from flask_login import current_user, login_required
from app.main.models import User, Location, Order, OrderItem
from app.main.models import Cart, Product, Location, Order, Arealine, UserDeliveryInfo, Location
from app.cart import cart_bp
from app.main.forms import CheckoutForm, LoginForm, userDeliveryInfoForm
from app import db, mail
from flask_mail import Message
from app.main import bp
from functools import wraps

from app import login_required



@cart_bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    quantity = int(request.form.get('quantity', 1))
    custom_description = request.form.get('custom_description', '')

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

    login_form = LoginForm()  # Replace with the actual form you're using

    return render_template('view_cart.html',
                           cart_items=cart_items,
                           total_price=total_price,
                           login_form=login_form)

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
def get_cart_count():
    try:
        if not current_user.is_authenticated:
            # Return 0 for guest users
            return jsonify({'status': 'not_logged_in', 'cart_count': 0}), 200

        cart_count = Cart.query.filter_by(user_id=current_user.id).count()
        return jsonify({'status': 'success', 'cart_count': cart_count}), 200
    except Exception as e:
        app.logger.error('Error fetching cart count: %s', str(e))
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
    checkout_form = CheckoutForm()
    delivery_info_form = userDeliveryInfoForm()
    login_form = LoginForm()

    # Set choices for dynamic fields
    delivery_info_form.set_location_choices(Location.query.all())
    delivery_info_form.set_arealine_choices(Arealine.query.all())

    # Fetch cart items and calculate total price
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total_price = sum(cart_item.product.unit_price * cart_item.quantity for cart_item in cart_items) + 200

    # Fetch latest delivery information
    delivery_info = UserDeliveryInfo.query.filter_by(user_id=current_user.id).order_by(UserDeliveryInfo.id.desc()).first()

    if checkout_form.validate_on_submit():
        # Check if the user wants to use saved address
        if 'use_saved_address' in request.form and request.form['use_saved_address'] == 'on':
            if not delivery_info:
                flash('Please add your shipping information before proceeding.', 'warning')
                return redirect(url_for('cart.checkout'))
        else:
            flash('You need to provide delivery information to proceed.', 'danger')
            return redirect(url_for('cart.checkout'))

        # Redirect to order summary page
        return redirect(url_for('cart.order_summary', total_price=total_price, delivery_info_id=delivery_info.id if delivery_info else None))

    return render_template('checkout.html', 
                           form=checkout_form,
                           cart_items=cart_items, 
                           total_price=total_price, 
                           login_form=login_form, 
                           delivery_info=delivery_info, 
                           delivery_info_form=delivery_info_form,
                           user=current_user,
                           has_delivery_info=bool(delivery_info)
                          )




@cart_bp.route('/delivery_info', methods=['POST'])
@login_required
def add_or_update_delivery_info():
    delivery_info_form = userDeliveryInfoForm()

    # Populate the choices for the dynamic fields
    delivery_info_form.set_location_choices(Location.query.all())
    delivery_info_form.set_arealine_choices(Arealine.query.all())

    if delivery_info_form.validate_on_submit():
        # Check if there's existing delivery info for the user
        delivery_info = UserDeliveryInfo.query.filter_by(user_id=current_user.id).first()

        if delivery_info:
            # Update the existing delivery info
            delivery_info.full_name = delivery_info_form.full_name.data
            delivery_info.phone_number = delivery_info_form.phone_number.data
            delivery_info.alt_phone_number = delivery_info_form.alt_phone_number.data
            delivery_info.location_id = delivery_info_form.location.data
            delivery_info.arealine_id = delivery_info_form.arealine.data
            delivery_info.nearest_place_id = delivery_info_form.nearest_place.data
            delivery_info.address_line = delivery_info_form.address_line.data

            flash('Delivery information updated successfully!', 'success')
        else:
            # Create new delivery info
            delivery_info = UserDeliveryInfo(
                user_id=current_user.id,  # Ensure user_id is set correctly
                full_name=delivery_info_form.full_name.data,
                phone_number=delivery_info_form.phone_number.data,
                alt_phone_number=delivery_info_form.alt_phone_number.data,
                location_id=delivery_info_form.location.data,
                arealine_id=delivery_info_form.arealine.data,
                nearest_place_id=delivery_info_form.nearest_place.data,  # Adjusted for FK
                address_line=delivery_info_form.address_line.data
            )

            db.session.add(delivery_info)
            flash('Delivery information added successfully!', 'success')

        db.session.commit()

        return redirect(url_for('cart.checkout'))

    flash('There was an error with your form submission. Please try again.', 'danger')
    return redirect(url_for('cart.checkout'))



@cart_bp.route('/order_summary', methods=['GET', 'POST'])
@login_required
def order_summary():
    form = CheckoutForm()
    # Retrieve cart items and calculate total price
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total_price = sum(cart_item.product.unit_price * cart_item.quantity for cart_item in cart_items) + 200
    
    # Fetch the most recent delivery info for the user
    delivery_info = UserDeliveryInfo.query.filter_by(user_id=current_user.id).order_by(UserDeliveryInfo.id.desc()).first()
    
    if not delivery_info:
        flash('No delivery information found. Please add your shipping information before proceeding.', 'warning')
        return redirect(url_for('cart.checkout'))

    # Retrieve related location, arealine, and nearest place
    location = Location.query.get(delivery_info.location_id)
    arealine = Arealine.query.get(delivery_info.arealine_id)
    
    if request.method == 'POST':
        # Finalize the order
        new_order = Order(
            user_id=current_user.id,
            total_price=total_price,
            delivery_info_id=delivery_info.id,
            phone_number=delivery_info.phone_number,
            payment_method=request.form.get('payment_method'),
            custom_description=request.form.get('custom_description', '')
        )

        db.session.add(new_order)
        db.session.commit()

        # Add order items to the order
        for cart_item in cart_items:
            order_item = OrderItem(
                order=new_order,
                product_id=cart_item.product.id,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.unit_price,
                custom_description=cart_item.custom_description
            )
            db.session.add(order_item)

        db.session.commit()

        # Clear the user's cart
        Cart.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        # Send order confirmation email to the user
        send_order_confirmation_email(current_user.email, 'afuyaah@gmail.com', new_order)

        # Clear the session information after the order is placed
        session.pop('delivery_info', None)

        # Flash success message and redirect
        flash('Your order has been successfully placed!', 'success')
        return redirect(url_for('main.recommendations', order_id=new_order.id))

    return render_template('order_summary.html',
                           cart_items=cart_items,
                           total_price=total_price,
                           delivery_info=delivery_info,
                           location=location,
                           arealine=arealine,
                           form=form
                          )





@cart_bp.route('/reorder/<int:order_id>', methods=['POST'])
@login_required
def reorder(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        if order.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        for item in order.order_items:
            product = Product.query.get(item.product_id)
            if not product:
                return jsonify({'error': f'Product with id {item.product_id} not found'}), 404

            # Update the price to the current price
            current_price = product.unit_price

            # Check if item already exists in the cart
            cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product.id).first()
            if cart_item:
                cart_item.quantity += item.quantity
                cart_item.unit_price = current_price  # Update to current price
            else:
                # Add to cart
                new_cart_item = Cart(
                    user_id=current_user.id,
                    product_id=product.id,
                    quantity=item.quantity,
                    
                    custom_description=item.custom_description
                )
                db.session.add(new_cart_item)

        db.session.commit()
        return redirect(url_for('cart.view_cart'))

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def send_order_confirmation_email(user_email, admin_email, order):
    try:
        # Define the subject and recipients
        user_subject = 'Order Confirmation - Your Order Was Successful'
        admin_subject = 'New Order Alert'

        # Render the HTML content for the user's email
        user_msg = Message(subject=user_subject,
                           sender=app.config['MAIL_USERNAME'],
                           recipients=[user_email])
        user_msg.html = render_template('emails/order_confirmation_user.html', order=order)

        # Send the user's confirmation email
        mail.send(user_msg)
        app.logger.info(f"Order confirmation email sent to {user_email}")

        # Render the HTML content for the admin's email
        admin_msg = Message(subject=admin_subject,
                            sender=app.config['MAIL_USERNAME'],
                            recipients=[admin_email])
        admin_msg.html = render_template('emails/order_confirmation_admin.html', order=order)

        # Send the admin's order alert email
        mail.send(admin_msg)
        app.logger.info(f"New order alert email sent to {admin_email}")

    except Exception as e:
        app.logger.error(f"Failed to send order confirmation email: {str(e)}")
        # Optionally, handle the error further or notify someone


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
