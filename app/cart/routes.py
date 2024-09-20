# Import necessary modules and classes
from flask import render_template, flash, redirect, url_for, request, jsonify, current_app as app, session
from flask_login import current_user, login_required
from app.main.models import User, Location, Order, OrderItem
from app.main.models import Cart, Product, Location, Order, Arealine, UserDeliveryInfo, Location, ProductVariety
from app.cart import cart_bp
from app.main.forms import CheckoutForm, LoginForm, userDeliveryInfoForm
from app import db, mail
from flask_mail import Message
from app.main import bp
from app import login_required, cart_access_required
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import OperationalError


@cart_bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    variety_id = request.form.get('variety_id')

    if quantity <= 0:
        return jsonify({'status': 'error', 'message': 'Invalid Quantity.'}), 400

    # Determine price and check stock based on selected variety
    selected_price = product.unit_price
    if variety_id:
        variety = ProductVariety.query.get(variety_id)
        if variety and variety.product_id == product.id:
            selected_price = variety.price
            if quantity > variety.quantity_in_stock:
                return jsonify({'status': 'error', 'message': 'Out of stock for selected variety.'}), 400
        else:
            return jsonify({'status': 'error', 'message': 'Invalid variety selected.'}), 400
    else:
        if quantity > product.quantity_in_stock:
            return jsonify({'status': 'error', 'message': 'Out of stock.'}), 400

    # Handling guest users
    if current_user.is_authenticated:
        cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product.id, product_variety_id=variety_id).first()
        if cart_item:
            cart_item.quantity += quantity
            cart_item.price = selected_price  # Update price if needed
        else:
            cart_item = Cart(user_id=current_user.id, product_id=product.id, product_variety_id=variety_id, quantity=quantity, price=selected_price)
            db.session.add(cart_item)
    else:
        # Manage guest cart in session
        if 'cart' not in session:
            session['cart'] = {}

        key = f"{product.id}_{variety_id}"  # Create a unique key for variety
        if key in session['cart']:
            session['cart'][key]['quantity'] += quantity
            session['cart'][key]['price'] = selected_price  # Update price if needed
        else:
            session['cart'][key] = {
                'quantity': quantity,
                'price': selected_price  # Store price for later use
            }

    # Update product or variety stock
    if variety_id:
        variety.quantity_in_stock -= quantity
        if variety.quantity_in_stock < 0:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': 'Insufficient stock for the selected variety.'}), 400
    else:
        product.quantity_in_stock -= quantity
        if product.quantity_in_stock < 0:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': 'Insufficient stock for the product.'}), 400

    try:
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Item added to cart successfully.'})
    except (IntegrityError, OperationalError) as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Database error occurred: {str(e)}'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'An unexpected error occurred: {str(e)}'}), 500


@cart_bp.route('/view_cart')
@login_required
def view_cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    total_price = sum(item.price * item.quantity for item in cart_items)

    login_form = LoginForm()  # Replace with the actual form you're using

    return render_template('view_cart.html',
                           cart_items=cart_items,
                           total_price=total_price,
                           login_form=login_form)

# Function to calculate the total amount in the cart
def calculate_total_amount():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total_amount = sum(item.price * item.quantity for item in cart_items)  # Use item.price
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
    try:
        cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        
        if cart_item:
            quantity = cart_item.quantity
            return jsonify({'status': 'success', 'data': {'quantity': quantity}})
        else:
            return jsonify({'status': 'success', 'data': {'quantity': 0}})

    except Exception as e:
        current_app.logger.error('Error fetching product quantity: %s', str(e))
        return jsonify({'status': 'error', 'message': 'An error occurred while fetching the quantity.'}), 500



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

        updated_cart_info = update_cart_in_database(user_id, product_id, action)

        response_data = {
            'status': 'success',
            'message': 'Cart updated successfully',
            'data': {
                'cartItems': updated_cart_info['cartItems'],
                'totalPrice': updated_cart_info['totalPrice'],
            }
        }

        return jsonify(response_data)

    except ValueError as ve:
        app.logger.warning('ValueError: %s', str(ve))
        response_data = {
            'status': 'error',
            'message': str(ve),  # Use the specific message from ValueError
        }
        return jsonify(response_data), 400

    except Exception as e:
        app.logger.error('Error updating cart: %s', str(e))
        response_data = {
            'status': 'error',
            'message': 'An error occurred. Please try again later.',
        }
        return jsonify(response_data), 500

def update_cart_in_database(user_id, product_id, action):
    try:
        cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
        product = Product.query.get(product_id)

        if action not in ['increment', 'decrement']:
            raise ValueError('Invalid action')

        if cart_item:
            if action == 'increment':
                if product and product.quantity_in_stock > 0:
                    cart_item.quantity += 1
                    product.quantity_in_stock -= 1
                else:
                    raise ValueError('This item is currently out of stock. Please check back later.')
            elif action == 'decrement' and cart_item.quantity > 1:
                cart_item.quantity -= 1
                product.quantity_in_stock += 1
        else:
            if action == 'increment' and product and product.quantity_in_stock > 0:
                cart_item = Cart(user_id=user_id, product_id=product_id, quantity=1)
                db.session.add(cart_item)
                product.quantity_in_stock -= 1
            else:
                raise ValueError('Cannot add item to cart as it is currently out of stock.')

        db.session.commit()

    except Exception as e:
        db.session.rollback()  # Rollback in case of an error
        raise e  # Reraise the error for handling in the caller

    return get_updated_cart_info(user_id)

def get_updated_cart_info(user_id):
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    total_price = sum(cart_item.product.unit_price * cart_item.quantity for cart_item in cart_items)

    return {
        'cartItems': [{
            'productId': item.product_id,
            'quantity': item.quantity,
            'subtotal': item.product.unit_price * item.quantity
        } for item in cart_items],
        'totalPrice': total_price,
    }
def get_authenticated_user_id():
    return current_user.get_id()


# Route to clear the cart
@bp.route('/main/cart/clear_cart', methods=['POST'])
def clear_cart():
    try:
        user_id = get_authenticated_user_id()

        if user_id is None:
            raise ValueError('User not authenticated')

        # Fetch all cart items for the user
        cart_items = Cart.query.filter_by(user_id=user_id).all()

        if not cart_items:
            return jsonify({
                'status': 'error',
                'message': 'No items in the cart to clear.'
            }), 400

        # Start a transaction for safety
        with db.session.begin():
            for cart_item in cart_items:
                product = cart_item.product

                # Update the product stock
                product.quantity_in_stock += cart_item.quantity

            # Clear the user's cart
            clear_cart_in_database(user_id)

        response_data = {
            'status': 'success',
            'message': 'Cart cleared successfully',
        }
        return jsonify(response_data)

    except Exception as e:
        # Roll back any changes in case of error
        db.session.rollback()
        current_app.logger.error('Error clearing cart: %s', str(e))

        response_data = {
            'status': 'error',
            'message': 'Internal Server Error: ' + str(e),
        }
        return jsonify(response_data), 500

# Function to clear the cart in the database
def clear_cart_in_database(user_id):
    Cart.query.filter_by(user_id=user_id).delete(synchronize_session=False)
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

        # Handle case where user opts not to use saved address but needs to provide new info
        elif delivery_info_form.validate_on_submit():
            # Add new delivery info here
            new_delivery_info = UserDeliveryInfo(
                user_id=current_user.id,
                location_id=delivery_info_form.location.data,
                arealine_id=delivery_info_form.arealine.data,
                address=delivery_info_form.address.data,
                phone_number=delivery_info_form.phone_number.data
            )
            db.session.add(new_delivery_info)
            db.session.commit()

            delivery_info = new_delivery_info  # Use the newly added delivery info

        else:
            # No valid saved address or new info provided
            flash('You need to provide delivery information to proceed.', 'danger')
            return redirect(url_for('cart.checkout'))

        # Redirect to order summary page with the chosen delivery info
        return redirect(url_for('cart.order_summary', total_price=total_price, delivery_info_id=delivery_info.id))

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

    # Populate the choices for dynamic fields
    delivery_info_form.set_location_choices(Location.query.all())
    delivery_info_form.set_arealine_choices(Arealine.query.all())

    if delivery_info_form.validate_on_submit():
        try:
            delivery_info = UserDeliveryInfo.query.filter_by(user_id=current_user.id).first()

            if delivery_info:
                # Update existing delivery info
                update_delivery_info(delivery_info, delivery_info_form)
                flash('Delivery information updated successfully!', 'success')
            else:
                # Create new delivery info
                delivery_info = UserDeliveryInfo(
                    user_id=current_user.id,
                    full_name=delivery_info_form.full_name.data,
                    phone_number=delivery_info_form.phone_number.data,
                    alt_phone_number=delivery_info_form.alt_phone_number.data,
                    location_id=delivery_info_form.location.data,
                    arealine_id=delivery_info_form.arealine.data,
                    nearest_place=delivery_info_form.nearest_place.data,
                    address_line=delivery_info_form.address_line.data
                )
                db.session.add(delivery_info)
                flash('Delivery information added successfully!', 'success')

            db.session.commit()
            return redirect(url_for('cart.checkout'))

        except Exception as e:
            db.session.rollback()  # Rollback in case of an error
            current_app.logger.error('Error adding/updating delivery info: %s', str(e))
            flash('There was an error processing your request. Please try again.', 'danger')

    flash('There was an error with your form submission. Please try again.', 'danger')
    return redirect(url_for('cart.checkout'))

def update_delivery_info(delivery_info, form):
    delivery_info.full_name = form.full_name.data
    delivery_info.phone_number = form.phone_number.data
    delivery_info.alt_phone_number = form.alt_phone_number.data
    delivery_info.location_id = form.location.data
    delivery_info.arealine_id = form.arealine.data
    delivery_info.nearest_place = form.nearest_place.data
    delivery_info.address_line = form.address_line.data


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
                product_variety_id=cart_item.product_variety.id if cart_item.product_variety else None,
                quantity=cart_item.quantity,
                unit_price=cart_item.price  # Use the actual price from the cart
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

        # Flash success message and redirect to recommendations page
        flash('Your order has been successfully placed!', 'success')
        return redirect(url_for('main.product_listing', order_id=new_order.id))

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

        cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

        if not cart_item:
            return jsonify({
                'status': 'error',
                'message': 'Item not found in cart.'
            }), 404

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

    except ValueError as ve:
        current_app.logger.warning('ValueError: %s', str(ve))
        response_data = {
            'status': 'error',
            'message': str(ve),
        }
        return jsonify(response_data), 400

    except Exception as e:
        current_app.logger.error('Error removing item from cart: %s', str(e))
        response_data = {
            'status': 'error',
            'message': 'An error occurred while removing the item. Please try again later.',
        }
        return jsonify(response_data), 500

# Function to remove item from the cart in the database
def remove_item_from_cart(user_id, product_id):
    cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

    if cart_item:
        product = Product.query.get(product_id)
        if product:
            product.quantity_in_stock += cart_item.quantity

        db.session.delete(cart_item)
        db.session.commit()
