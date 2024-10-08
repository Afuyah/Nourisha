from app import db, mail, admin_required, login_required
from flask import render_template, abort, flash, redirect, url_for, request, jsonify, session,Flask, current_app as app
from flask_login import current_user, login_user, logout_user

from app.main import bp
from app.main.forms import AddProductCategoryForm, AddProductForm, ProductImageForm, AddProductForm, AddRoleForm, AddSupplierForm,RecommendationForm,LoginForm, UnitOfMeasurementForm
from app.main.models import User, Role, Cart, Supplier, ProductImage, ProductCategory, Product, Order, OrderItem, Offer, AboutUs ,BlogPost, ContactMessage, UnitOfMeasurement, ProductVariety
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from sqlalchemy.orm.exc import NoResultFound
from app.cart.routes import cart_bp
from .send_email import send_confirmation_email
from sqlalchemy import func, desc
from flask_mail import Message
from functools import wraps
from dateutil import parser
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

import re
import os
import random 
import uuid

@bp.route('/refresh_csrf_token', methods=['GET'])
def refresh_csrf_token():
    # Generate a new CSRF token
    new_csrf_token = generate_csrf_token()  # Implement your token generation logic here

    # Get the expiration time for the new token (assuming a fixed expiration time)
    # You can adjust this as per your application's requirements
    expiration_time = datetime.utcnow() + timedelta(minutes=30)  # Example: Token expires in 30 minutes

    # Return the new CSRF token and its expiration time as JSON response
    return jsonify({'csrf_token': new_csrf_token, 'expiration_time': expiration_time.strftime('%Y-%m-%dT%H:%M:%SZ')})







# Instantiate the URLSafeTimedSerializer with a secret key
serializer = URLSafeTimedSerializer('mysecretkey')


def send_email(to, subject, body):
  msg = Message(subject, recipients=[to])
  msg.body = body
  mail.send(msg)


@bp.route('/', methods=['GET', 'POST'])
def index():
    user_authenticated = current_user.is_authenticated
    offers = Offer.query.filter_by(active=True).all()
    categories = ProductCategory.query.all()  # Fetch the categories
    about_us = AboutUs.query.first()
    blog_posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).limit(3).all() 
    
    login_form = LoginForm()
    return render_template('home.html',
                           title='Home',
                           product_listing_url=url_for('main.product_listing'),
                           user_authenticated=user_authenticated, 
                           offers=offers, 
                           categories=categories,
                           about_us=about_us,
                           blog_posts=blog_posts,
                           login_form=login_form)


@bp.route('/contact', methods=['POST'])
def contact():
                       form = ContactForm(request.form)  # Ensure form is instantiated with request data
                       print('Form data:', request.form)  # Log the received form data
                       if form.validate_on_submit():
                           contact_message = ContactMessage(
                               name=form.name.data,
                               email=form.email.data,
                               message=form.message.data
                           )
                           try:
                               db.session.add(contact_message)
                               db.session.commit()
                               return jsonify({'success': ' Thank you for contacting us! We will get back to you soon!'})
                           except Exception as e:
                               db.session.rollback()
                               return jsonify({'error': f'Error sending message: {e}'})
                       else:
                           # Log form errors
                           errors = form.errors
                           print('Form errors:', errors)
                           return jsonify({'error': 'Invalid input', 'form_errors': errors})

@bp.route('/dashboard')
@login_required
def user_dashboard():
  # Fetch user information from the database
  user = User.query.filter_by(id=current_user.id).first()
  login_form=LoginForm()
  # Fetch user's orders from the database
  
  orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
  return render_template('user_dashboard.html', user=user, orders=orders, login_form=login_form)

def send_welcome_email(user):
  msg = Message('Welcome to Our Application!', recipients=[user.email])
  msg.body = f"Dear {user.username},\n\nWelcome to Nourisha!!! We're excited to have you on board."
  # You can also use HTML for the email body:
  # msg.html = render_template('welcome_email.html', user=user)
  mail.send(msg)

# Regular expression to match phone number format: 07xxxxxxxx
def is_valid_phone_number(phone):
    return bool(re.match(r'^07\d{8}$', phone))

def generate_confirmation_token(user_id):
    return serializer.dumps(user_id)

def send_confirmation_email(user, token):
    confirm_url = url_for('main.confirm_email', token=token, _external=True)
    subject = 'Confirm Your Email Address'
    body = f"Thank you for joining! Please click the following link to confirm your email address: {confirm_url}"
    send_email(user.email, subject, body)

def is_strong_password(password):
    return len(password) >= 4

def is_valid_email(email):
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email))

@bp.route('/confirm_email/<token>', methods=['GET'])
def confirm_email(token):
    try:
        user_id = serializer.loads(token, max_age=3600)  # Token expires in 1 hour
        user = User.query.get(int(user_id))  # Ensure user_id is converted to int

        if user and not user.confirmed:
            user.confirmed = True
            db.session.commit()
            flash('Email confirmation successful! You can now log in.', 'success')
        elif user and user.confirmed:
            flash('Email already confirmed. You can log in.', 'info')
        else:
            flash('Invalid confirmation link. Please contact support.', 'danger')

    except SignatureExpired:
        flash('The confirmation link has expired. Please register again.', 'danger')
    except BadSignature:
        flash('Invalid confirmation link. Please contact support.', 'danger')
    except Exception as e:
        flash(f'Error confirming email: {str(e)}', 'danger')
        app.logger.error(f"Error confirming email: {e}")

    return redirect(url_for('main.login'))

from flask_login import login_user






@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

    login_time = session.get('login_time')

    if login_time:
        utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        session_duration = utc_now - login_time
        session['average_session_duration'] = session_duration.total_seconds()
        session['login_time'] = utc_now


@bp.route('/check_authentication', methods=['GET'])
def check_authentication():
    return jsonify({'is_authenticated': current_user.is_authenticated})



@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/featured-categories')
def featured_categories():
    categories = ProductCategory.query.all()
    random.shuffle(categories)  # Shuffle the categories list
    return render_template('home.html', categories=categories)



@bp.route('/add_product_category', methods=['GET', 'POST'])
@admin_required
def add_product_category():
  form = AddProductCategoryForm()

  if form.validate_on_submit():
    # Handle form submission and add the new category to the database
    category_name = form.name.data
    category = ProductCategory(name=category_name)
    db.session.add(category)
    db.session.commit()
    flash('Product category added successfully', 'success')
    return redirect(url_for('main.add_product_category'))

  # Fetch all product categories from the database
  categories = ProductCategory.query.all()

  return render_template('add_product_category.html',
                         form=form,
                         categories=categories)


@bp.route('/add_supplier', methods=['GET', 'POST'])
@admin_required
def add_supplier():
    form = AddSupplierForm()

    if form.validate_on_submit():
        supplier = Supplier(
            supplier_id=form.supplier_id.data,
            name=form.name.data,
            contact_person=form.contact_person.data,
            contact_email=form.contact_email.data,
            contact_phone=form.contact_phone.data,
            address=form.address.data,
            city=form.city.data
        )
        try:
            db.session.add(supplier)
            db.session.commit()
            flash('Supplier added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding supplier: {str(e)}', 'danger')
        return redirect(url_for('main.add_supplier'))

    suppliers = Supplier.query.all()
    return render_template('add_supplier.html', form=form, suppliers=suppliers)


@bp.route('/edit_supplier/<int:supplier_id>', methods=['GET', 'POST'])
@admin_required
def edit_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    form = AddSupplierForm(obj=supplier)

    if form.validate_on_submit():
        supplier.supplier_id = form.supplier_id.data
        supplier.name = form.name.data
        supplier.contact_person = form.contact_person.data
        supplier.contact_email = form.contact_email.data
        supplier.contact_phone = form.contact_phone.data
        supplier.address = form.address.data
        supplier.city = form.city.data

        try:
            db.session.commit()
            flash('Supplier updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating supplier: {str(e)}', 'danger')
        return redirect(url_for('main.add_supplier'))

    return render_template('edit_supplier.html', form=form, supplier=supplier)


@bp.route('/get_supplier_details', methods=['GET'])
@admin_required
def get_supplier_details():
    supplier_id = request.args.get('supplier_id', type=int)
    supplier = Supplier.query.get_or_404(supplier_id)
    supplier_data = {
        'supplier_id': supplier.supplier_id,
        'name': supplier.name,
        'contact_person': supplier.contact_person,
        'contact_email': supplier.contact_email,
        'contact_phone': supplier.contact_phone,
        'address': supplier.address,
        'city': supplier.city,
    }
    return jsonify(supplier_data)

@bp.route('/delete_supplier/<int:supplier_id>', methods=['POST'])
@admin_required
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    try:
        db.session.delete(supplier)
        db.session.commit()
        flash('Supplier deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting supplier: {str(e)}', 'danger')
    return redirect(url_for('main.add_supplier'))


@bp.route('/add_product', methods=['GET', 'POST'])
@admin_required
def add_product():
    form = AddProductForm()
    image_form = ProductImageForm()

    # Populate choices for select fields
    image_form.product.choices = [(product.id, product.name) for product in Product.query.all()]
    form.supplier.choices = [(supplier.id, supplier.name) for supplier in Supplier.query.all()]
    form.category.choices = [(category.id, category.name) for category in ProductCategory.query.all()]
    form.unit_measurement.choices = [(unit.id, unit.unit) for unit in UnitOfMeasurement.query.all()]

    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            category_id=form.category.data,
            brand=form.brand.data,
            unit_price=form.unit_price.data,
            unit_measurement_id=form.unit_measurement.data,
            quantity_in_stock=form.quantity_in_stock.data,
            discount_percentage=form.discount_percentage.data,
            nutritional_information=form.nutritional_information.data,
            country_of_origin=form.country_of_origin.data,
            supplier_id=form.supplier.data,
            
        )

        db.session.add(product)
        db.session.commit()

        flash('Product added successfully!', 'success')
        return redirect(url_for('main.add_product'))

    return render_template('add_product.html', form=form, image_form=image_form)




def generate_sku(product_id, size_name, color_name, weight):
    base_sku = f"{product_id}-{size_name[:2].upper() if size_name else ''}{color_name[:2].upper() if color_name else ''}{weight.upper() if weight else ''}"
    unique_id = uuid.uuid4().hex[:6].upper()  # Shortened UUID for SKU uniqueness
    return f"{base_sku}-{unique_id}"


@bp.route('/add_unit_of_measurement', methods=['GET', 'POST'])
@admin_required
def add_unit_of_measurement():
    form = UnitOfMeasurementForm()

    if form.validate_on_submit():
        try:
            unit = UnitOfMeasurement(
                unit=form.unit.data,
                added_by=current_user.username,  # Assuming current_user has a username attribute
                date_added=datetime.utcnow()
            )

            db.session.add(unit)
            db.session.commit()

            flash('Unit of Measurement added successfully!', 'success')
            return redirect(url_for('main.add_unit_of_measurement'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')

    return render_template('add_unit_of_measurement.html', form=form)

@bp.route('/view_product/<int:product_id>')
@login_required
def view_product(product_id):
  product = Product.query.get_or_404(product_id)
  return render_template('view_product.html', product=product)


@bp.route('/products')
@login_required
def products():
  products = Product.query.all()
  return render_template('products.html', products=products)


@bp.route('/add_product_image', methods=['GET', 'POST'])
@admin_required
def add_product_image():
    form = ProductImageForm()

    # Populate the product choices in the form
    form.product.choices = [(product.id, product.brand) for product in Product.query.all()]

    if form.validate_on_submit():
        product_id = form.product.data
        cover_image = form.cover_image.data
        image1 = form.image1.data
        image2 = form.image2.data
        image3 = form.image3.data

        try:
            # Create the folder if it does not exist
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)

            # Save cover image (with validation)
            cover_filename = save_image(cover_image, upload_folder)
            cover_image_entry = ProductImage(product_id=product_id, image_path=cover_filename, is_cover=True)
            db.session.add(cover_image_entry)

            # Save additional images (with validation)
            for image_data in [image1, image2, image3]:
                if image_data:
                    filename = save_image(image_data, upload_folder)
                    image_entry = ProductImage(product_id=product_id, image_path=filename, is_cover=False)
                    db.session.add(image_entry)

            db.session.commit()
            flash('Images uploaded successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while uploading images: {str(e)}', 'danger')

        return redirect(url_for('main.add_product_image'))

    return render_template('add_product_image.html', form=form)

def save_image(image_data, upload_folder):
    # Validate the image type and size
    validate_image(image_data)

    # Generate a unique filename
    filename = generate_unique_filename(image_data.filename)
    file_path = os.path.join(upload_folder, filename)
    
    # Save the image
    image_data.save(file_path)
    return filename

def validate_image(image_data):
    # Check the file extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    extension = os.path.splitext(image_data.filename)[1].lower().replace('.', '')
    if extension not in allowed_extensions:
        raise ValueError(f"File type not allowed: {extension}")

    # Validate image size (e.g., max 5MB)
    if len(image_data.read()) > 5 * 1024 * 1024:  # 5MB limit
        raise ValueError("Image exceeds size limit of 5MB")
    image_data.seek(0)  # Reset file pointer after reading

    # Check image validity using Pillow
    try:
        image = Image.open(image_data)
        image.verify()  # Check if it's a valid image
    except Exception:
        raise ValueError("Invalid image file")

def generate_unique_filename(original_filename):
    filename, extension = os.path.splitext(secure_filename(original_filename))
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    unique_filename = f"{filename}_{timestamp}{extension}"
    return unique_filename





@bp.route('/product_details/<int:product_id>')
def product_details(product_id):
  try:
    # Perform a join query to fetch product and associated images
    product_data = db.session.query(Product, ProductImage).\
        join(ProductImage, Product.id == ProductImage.product_id).\
        filter(Product.id == product_id).first()

    if not product_data:
      # Handle the case where the product with the given ID is not found
      abort(404)

    product, images = product_data

    return render_template('product_details.html',
                           product=product,
                           images=[images])  # Wrap images in a list

  except NoResultFound:
    # Handle the case where the product with the given ID is not found
    abort(404)

@bp.route('/product_listing')
def product_listing():
    categories = ProductCategory.query.all()
    products = Product.query.all()

    # Convert the dynamic query object to a list
    for product in products:
        product.images = list(product.images)  # Convert AppenderQuery to list

    add_product_form = AddProductForm()
    login_form = LoginForm()
    return render_template('product_listing.html', categories=categories, form=add_product_form, products=products, login_form=login_form)



@bp.route('/product_listing/<int:category_id>')
def product_listing_by_category(category_id):
    category = ProductCategory.query.get_or_404(category_id)
    products = Product.query.filter_by(category=category).all()

    # Ensure images are converted to lists
    for product in products:
        product.images = list(product.images)  # Convert AppenderQuery to list

    categories = ProductCategory.query.all()
    add_product_form = AddProductForm()
    login_form = LoginForm()
    return render_template('product_listing.html', category=category, products=products, categories=categories, form=add_product_form, login_form=login_form)



@bp.route('/my-orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
    return render_template('my_orders.html', orders=orders)


@bp.route('/view_order/<int:order_id>')
@login_required
def view_order(order_id):
    login_form = LoginForm()
    order = Order.query.get_or_404(order_id)
    return render_template('user_view_order.html', order=order, login_form=login_form)

@bp.route('/search', methods=['GET', 'POST'])
def search():
    query = request.args.get('query', '')
    products = Product.query.filter(Product.name.ilike(f"%{query}%")).all()
    form = AddProductForm()
    return render_template('product_listing.html', products=products, form=form)

# Get user interactions
def get_user_interactions(user_id):
    interactions = db.session.query(Product).join(OrderItem).join(Order).filter(Order.user_id == user_id).all()
    return interactions

# Collaborative Filtering (User-Based)
def get_similar_users(user_id, top_n=5):
    user_interactions = db.session.query(Product.id).join(OrderItem).join(Order).filter(Order.user_id == user_id).all()
    user_interactions = [product.id for product in user_interactions]

    similar_users = db.session.query(Order.user_id).join(OrderItem).filter(OrderItem.product_id.in_(user_interactions)).filter(Order.user_id != user_id).group_by(Order.user_id).all()

    user_scores = []
    for similar_user_id in similar_users:
        shared_interactions = db.session.query(func.count(OrderItem.product_id)).join(Order).filter(Order.user_id == similar_user_id[0]).filter(OrderItem.product_id.in_(user_interactions)).scalar()
        user_scores.append((similar_user_id[0], shared_interactions))

    user_scores.sort(key=lambda x: x[1], reverse=True)
    top_similar_users = [user[0] for user in user_scores[:top_n]]

    return top_similar_users



# Content-Based Recommendations
def get_content_based_recommendations(product, top_n=5):
    similar_products = db.session.query(Product).filter(
        (Product.category_id == product.category_id) | 
        (Product.promotional_tag == product.promotional_tag)
    ).filter(Product.id != product.id).limit(top_n).all()
    return similar_products

# Popularity-Based Recommendations
def get_most_popular_products(top_n=10):
    return db.session.query(Product).order_by(Product.click_count.desc()).limit(top_n).all()

# Personalized Recommendations
def get_personalized_recommendations(user, top_n=10):
    favorite_categories = (
        db.session.query(Product.category_id, func.count(Product.category_id).label('count'))
        .join(OrderItem)
        .join(Order)
        .filter(Order.user_id == user.id)
        .group_by(Product.category_id)
        .order_by(desc('count'))
        .limit(3)
    )

    recommendations = []
    for category, _ in favorite_categories:
        recommendations.extend(db.session.query(Product).filter(Product.category_id == category).limit(top_n).all())

    return recommendations[:top_n]

# Final Recommender System
def recommend_products(user_id, num_recommendations=10):
    user = User.query.get(user_id)
    if not user:
        return []

    recommendations = []

    # Collaborative Filtering (User-Based)
    similar_users = get_similar_users(user_id)
    for similar_user_id in similar_users:
        recommendations.extend(get_user_interactions(similar_user_id))

   

   

    # Popularity-Based Recommendations
    recommendations.extend(get_most_popular_products())

    # Personalized Recommendations
    recommendations.extend(get_personalized_recommendations(user))

    # Ensure recommendations are unique based on product ID and are product objects
    recommendations = list({p.id: p for p in recommendations if hasattr(p, 'id')}.values())
    return recommendations[:num_recommendations]

# Route for getting product recommendations
@bp.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    try:
        user_id = request.args.get('user_id')
        num_recommendations = int(request.args.get('num', 10))

        if user_id:
            recommendations = recommend_products(int(user_id), num_recommendations)
        else:
            recommendations = get_most_popular_products(num_recommendations)

        return jsonify([{
            'id': product.id,
            'name': product.name,
            'brand': product.brand,
            'price': product.unit_price,
            'image': product.images[0].cover_image if product.images else None,
            'description': product.nutritional_information
        } for product in recommendations]), 200

    except Exception as e:
        app.logger.error(f"Error fetching recommendations: {e}", exc_info=True)
        return jsonify({'error': 'Server error'}), 500

# Route for tracking product events
@bp.route('/api/track-product-event', methods=['POST'])
def track_event():
    try:
        # Extract data from request
        data = request.json
        app.logger.debug(f"Request data: {data}")

        product_id = data.get('productId')
        event_type = data.get('eventType')
        timestamp = data.get('timestamp')

        if not product_id or not event_type or not timestamp:
            app.logger.warning(f"Missing data: productId={product_id}, eventType={event_type}, timestamp={timestamp}")
            return jsonify({'error': 'Missing data in request'}), 400

        try:
            parsed_timestamp = parser.parse(timestamp)
            app.logger.debug(f"Parsed timestamp: {parsed_timestamp}")
        except ValueError as ve:
            app.logger.warning(f"Invalid timestamp format: {timestamp} - {ve}")
            return jsonify({'error': 'Invalid timestamp format'}), 400

        user_id = get_current_user_id()
        guest_ip = get_client_ip() if not user_id else None
        app.logger.debug(f"User ID: {user_id}, Guest IP: {guest_ip}")

        if event_type == 'click':
            record_click_event(user_id, guest_ip, product_id, parsed_timestamp)
        elif event_type == 'view':
            record_view_event(user_id, guest_ip, product_id, parsed_timestamp)
        else:
            app.logger.warning(f"Invalid event type: {event_type}")
            return jsonify({'error': 'Invalid event type'}), 400

        app.logger.info(f"Event tracked successfully: productId={product_id}, eventType={event_type}")
        return jsonify({'message': 'Event tracked successfully'}), 200
    except Exception as e:
        app.logger.error(f"Error tracking event: {e}", exc_info=True)
        return jsonify({'error': 'Server error'}), 500

def record_click_event(user_id, guest_ip, product_id, timestamp):
    try:
        new_click = ProductClick(
            user_id=user_id,
            guest_ip=guest_ip,
            product_id=product_id,
            timestamp=timestamp
        )
        db.session.add(new_click)
        app.logger.debug(f"Added click event: {new_click}")

        product = Product.query.get(product_id)
        if product:
            product.click_count += 1
            db.session.commit()
            app.logger.info(f"Updated product click count: {product_id}, clickCount={product.click_count}")
        else:
            app.logger.warning(f"Product with ID {product_id} not found.")
            db.session.rollback()
    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemy error recording click event: {e}", exc_info=True)
        db.session.rollback()
        raise e
    except Exception as e:
        app.logger.error(f"Error recording click event: {e}", exc_info=True)
        db.session.rollback()
        raise e

def record_view_event(user_id, guest_ip, product_id, timestamp):
    try:
        new_view = ProductView(
            user_id=user_id,
            guest_ip=guest_ip,
            product_id=product_id,
            timestamp=timestamp
        )
        db.session.add(new_view)
        app.logger.debug(f"Added view event: {new_view}")

        product = Product.query.get(product_id)
        if product:
            product.view_count += 1
            db.session.commit()
            app.logger.info(f"Updated product view count: {product_id}, viewCount={product.view_count}")
        else:
            app.logger.warning(f"Product with ID {product_id} not found.")
            db.session.rollback()
    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemy error recording view event: {e}", exc_info=True)
        db.session.rollback()
        raise e
    except Exception as e:
        app.logger.error(f"Error recording view event: {e}", exc_info=True)
        db.session.rollback()
        raise e

def get_current_user_id():
    if current_user.is_authenticated:
        return current_user.id
    else:
        ip_address = request.remote_addr
        app.logger.debug(f"Guest IP address: {ip_address}")
        return ip_address

def get_client_ip():
    return request.remote_addr

# Route for rendering recommendations page
@bp.route('/recommendations')
def recommendations():
    recommendations = Product.query.all()
    
    # Convert AppenderQuery to list
    for product in recommendations:
        product.images = list(product.images)
    
    return render_template('recommendations.html', recommendations=recommendations)