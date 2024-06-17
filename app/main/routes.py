 
from app import db, mail
from flask import render_template, abort, flash, redirect, url_for, request, jsonify, session,Flask
from flask_login import current_user, login_user, logout_user, login_required
from app.main import bp
from app.main.forms import AddProductCategoryForm, AddProductForm, ProductImageForm, AddProductForm, RegistrationForm, LoginForm, AddRoleForm, AddSupplierForm
from app.main.models import User, Role, Cart, Supplier, ProductImage, ProductCategory, Product, Order, ProductView, ProductClick
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.orm.exc import NoResultFound
from app.cart.routes import cart_bp
from .send_email import send_confirmation_email

from flask_mail import Message
from functools import wraps
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy.orm.exc import NoResultFound
import re
import os
import logging



@bp.route('/refresh_csrf_token', methods=['GET'])
def refresh_csrf_token():
    # Generate a new CSRF token
    new_csrf_token = generate_csrf_token()  # Implement your token generation logic here

    # Get the expiration time for the new token (assuming a fixed expiration time)
    # You can adjust this as per your application's requirements
    expiration_time = datetime.utcnow() + timedelta(minutes=30)  # Example: Token expires in 30 minutes

    # Return the new CSRF token and its expiration time as JSON response
    return jsonify({'csrf_token': new_csrf_token, 'expiration_time': expiration_time.strftime('%Y-%m-%dT%H:%M:%SZ')})




def login_required(func):

  @wraps(func)
  def decorated_function(*args, **kwargs):
    if not current_user.is_authenticated:
      flash('Please login to access this page.', 'warning')
      return redirect(url_for('main.login', next=request.url))
    return func(*args, **kwargs)

  return decorated_function


# Instantiate the URLSafeTimedSerializer with a secret key
serializer = URLSafeTimedSerializer('mysecretkey')


def send_email(to, subject, body):
  msg = Message(subject, recipients=[to])
  msg.body = body
  mail.send(msg)


@bp.route('/')
def index():
  user_authenticated = current_user.is_authenticated
  return render_template('home.html',
                         title='Home',
                         product_listing_url=url_for('main.product_listing'),
                         user_authenticated=user_authenticated)


@bp.route('/dashboard')
@login_required
def user_dashboard():
  # Fetch user information from the database
  user = User.query.filter_by(id=current_user.id).first()

  # Fetch user's orders from the database
  orders = Order.query.filter_by(user_id=current_user.id).all()

  return render_template('user_dashboard.html', user=user, orders=orders)

def send_welcome_email(user):
  msg = Message('Welcome to Our Application!', recipients=[user.email])
  msg.body = f"Dear {user.username},\n\nWelcome to our application! We're excited to have you on board."
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

@bp.route('/register', methods=['POST', 'GET'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            # Create a new user instance
            user = User(
                username=form.username.data,
                email=form.email.data,
                phone=form.phone.data,
                name=form.name.data,
            )

            # Set the user password
            user.set_password(form.password.data)

            # Set confirmed to True to allow immediate login
            user.confirmed = True

            # Add the user to the database
            db.session.add(user)
            db.session.commit()

            # Automatically log in the user after registration
            login_user(user)

            # Send welcome email to the user
            send_welcome_email(user)

            flash(f'Registration successful! You are now logged in as {current_user.username}.!', 'success')
            return redirect(url_for('main.index'))

        except IntegrityError:
            db.session.rollback()
            flash('Email address is already registered. Please use Sign In.', 'danger')
            return redirect(url_for('main.login'))

    return render_template('register.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'POST' and form.validate_on_submit():
        identifier = form.identifier.data
        password = form.password.data

        # Check if the identifier is an email
        user = User.query.filter_by(email=identifier).first()

        # If not found, check if it's a phone number
        if not user:
            user = User.query.filter_by(phone=identifier).first()

        # If still not found, check if it's a username
        if not user:
            user = User.query.filter_by(username=identifier).first()

        if user and user.check_password(password):
            if user.confirmed:
                login_user(user)
                session['login_time'] = datetime.utcnow()
                user.last_login_date = datetime.utcnow()
                user.last_login_ip = request.remote_addr
                db.session.commit()
                flash(f'Welcome back, {current_user.username}!', 'success')

                if user.role and user.role.name == 'admin':
                    return redirect(url_for('admin.admin_dashboard'))

                return redirect(url_for('main.index'))
            else:
                flash('Your account is not confirmed. Please check your email for the confirmation link.', 'warning')
        else:
            flash('Invalid credentials. Please check your username/email/phone number and password.', 'danger')

    return render_template('login.html', form=form)

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

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/add_role', methods=['GET', 'POST'])
@login_required
def add_role():
  form = AddRoleForm()

  if form.validate_on_submit():
    role = Role(name=form.name.data)
    db.session.add(role)
    db.session.commit()
    flash('Role added successfully!', 'success')
    return redirect(url_for('main.add_role'))

  roles = Role.query.all()

  return render_template('add_role.html', form=form, roles=roles)


@bp.route('/add_product_category', methods=['GET', 'POST'])
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
@login_required
def add_supplier():
  form = AddSupplierForm()

  if form.validate_on_submit():
    # Create a new supplier using the form data
    supplier = Supplier(supplier_id=form.supplier_id.data,
                        name=form.name.data,
                        contact_person=form.contact_person.data,
                        contact_email=form.contact_email.data,
                        contact_phone=form.contact_phone.data,
                        address=form.address.data,
                        city=form.city.data)

    # Add and commit the new supplier to the database
    db.session.add(supplier)
    db.session.commit()

    flash('Supplier added successfully!', 'success')
    return redirect(url_for('main.add_supplier'))

  # Fetch all suppliers
  suppliers = Supplier.query.all()

  return render_template('add_supplier.html', form=form, suppliers=suppliers)


@bp.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
  form = AddProductForm()
  image_form = ProductImageForm()
  # Populate choices for select fields
  image_form.product.choices = [(product.id, product.name)
                                for product in Product.query.all()]
  form.supplier.choices = [(supplier.id, supplier.name)
                           for supplier in Supplier.query.all()]
  form.category.choices = [(category.id, category.name)
                           for category in ProductCategory.query.all()]

  if form.validate_on_submit():
    # Create a new product using the form data
    product = Product(
        name=form.name.data,
        category_id=form.category.data,
        brand=form.brand.data,
        unit_price=form.unit_price.data,
        unit_measurement=form.unit_measurement.data,
        quantity_in_stock=form.quantity_in_stock.data,
        discount_percentage=form.discount_percentage.data,
        promotional_tag=form.promotional_tag.data,
        nutritional_information=form.nutritional_information.data,
        country_of_origin=form.country_of_origin.data,
        supplier_id=form.supplier.data,
        date_added=form.date_added.data)

    # Add and commit the new product to the database
    db.session.add(product)
    db.session.commit()

    flash('Product added successfully!', 'success')
    return redirect(url_for('main.add_product'))

  # Fetch all products for display
  products = Product.query.all()

  return render_template('add_product.html',
                         form=form,
                         products=products,
                         image_form=image_form)


# Additional routes for viewing, editing, and deleting products can be added here
# Example:
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
@login_required
def add_product_image():
  form = ProductImageForm()

  # Populate the product choices in the form
  form.product.choices = [(product.id, product.name)
                          for product in Product.query.all()]

  if form.validate_on_submit():
    # Handle image uploads and save links to the database
    product_id = form.product.data
    cover_image = form.cover_image.data
    image1 = form.image1.data
    image2 = form.image2.data
    image3 = form.image3.data

    # Save cover image
    cover_filename = save_image(cover_image)
    cover_image_entry = ProductImage(product_id=product_id,
                                     cover_image=cover_filename)
    db.session.add(cover_image_entry)

    # Save additional images
    for image_data in [image1, image2, image3]:
      if image_data:
        filename = save_image(image_data)
        image_entry = ProductImage(product_id=product_id, cover_image=filename)
        db.session.add(image_entry)

    db.session.commit()
    flash('Images uploaded successfully', 'success')
    return redirect(url_for('main.add_product_image'))

  return render_template('add_product_image.html', form=form)


def save_image(image_data):
    
    filename = generate_unique_filename(image_data.filename)
    image_data.save(os.path.join('app', 'static', 'uploads', filename))
    return filename


def generate_unique_filename(original_filename):
    filename, extension = os.path.splitext(original_filename)
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    unique_filename = f"{secure_filename(filename)}_{timestamp}{extension}"
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


# Route to render the product listing page with categories
@bp.route('/product_listing')
def product_listing():
    categories = ProductCategory.query.all()
    products = Product.query.all()
    form = AddProductForm()
    return render_template('product_listing.html', categories=categories, form=form, products=products)

# Route to render the product listing based on the selected category
@bp.route('/product_listing/<int:category_id>')
def product_listing_by_category(category_id):
    category = ProductCategory.query.get_or_404(category_id)
    products = Product.query.filter_by(category=category).all()
    categories = ProductCategory.query.all()  # Fetch all categories to display in the carousel
    form = AddProductForm()
    return render_template('product_listing.html', category=category, products=products, categories=categories, form=form)

@bp.route('/view_order/<int:order_id>')
@login_required
def view_order(order_id):
  order = Order.query.get_or_404(order_id)
  return render_template('user_view_order.html', order=order)

@bp.route('/search', methods=['GET', 'POST'])
def search():
    query = request.args.get('query', '')
    products = Product.query.filter(Product.name.ilike(f"%{query}%")).all()
    form= AddProductForm()
    return render_template('product_listing.html', products=products, form=form)

#product recommendation section
#Collaborative Filtering (User-Based)
def get_similar_users(user_id, top_n=5):
    # Get the list of products the current user has interacted with
    user_interactions = db.session.query(Product.id).join(OrderItem).join(Order).filter(Order.user_id == user_id).all()
    user_interactions = [product.id for product in user_interactions]

    # Find other users who interacted with the same products
    similar_users = db.session.query(Order.user_id).join(OrderItem).filter(OrderItem.product_id.in_(user_interactions)).filter(Order.user_id != user_id).group_by(Order.user_id).all()

    # Optionally, we could score users based on the number of shared interactions
    user_scores = []
    for similar_user_id in similar_users:
        shared_interactions = db.session.query(func.count(OrderItem.product_id)).join(Order).filter(Order.user_id == similar_user_id[0]).filter(OrderItem.product_id.in_(user_interactions)).scalar()
        user_scores.append((similar_user_id[0], shared_interactions))

    # Sort by shared interactions and return the top N similar users
    user_scores.sort(key=lambda x: x[1], reverse=True)
    top_similar_users = [user[0] for user in user_scores[:top_n]]

    return top_similar_users

#Collaborative Filtering (Item-Based)

def get_similar_products(product, top_n=5):
   
    # Get all products' descriptions (or other attributes)
    products = db.session.query(Product).all()
    product_descriptions = [p.description for p in products]
    product_ids = [p.id for p in products]

    # Create a TF-IDF vectorizer and fit it on product descriptions
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(product_descriptions)

    # Get the TF-IDF vector for the current product
    product_idx = product_ids.index(product.id)
    product_vector = tfidf_matrix[product_idx]

    # Compute cosine similarity between the current product and all other products
    cosine_sim = cosine_similarity(product_vector, tfidf_matrix)
    similar_indices = cosine_sim.argsort().flatten()[-(top_n+1):-1]  # Exclude the product itself

    similar_products = [product_ids[i] for i in similar_indices]
    return similar_products

#Content-Based Recommendations

def get_content_based_recommendations(product, top_n=5):
    # Example: Finding similar products based on category and tags
    similar_products = db.session.query(Product).filter(
        (Product.category_id == product.category_id) | 
        (Product.promotional_tag == product.promotional_tag)
    ).filter(Product.id != product.id).limit(top_n).all()

    return similar_products

#Popularity-Based Recommendations

def get_most_popular_products(top_n=10):
    popular_products = db.session.query(Product).order_by(Product.click_count.desc()).limit(top_n).all()
    return popular_products

#persoanlized recommendations
def get_personalized_recommendations(user, top_n=10):
    # Personalized recommendations might include products in the user's frequently purchased categories
    favorite_categories = db.session.query(Product.category_id, func.count(Product.category_id).label('count')).join(OrderItem).join(Order).filter(Order.user_id == user.id).group_by(Product.category_id).order_by('count DESC').limit(3).all()

    recommendations = []
    for category, _ in favorite_categories:
        recommendations.extend(db.session.query(Product).filter(Product.category_id == category).limit(top_n).all())

    return recommendations[:top_n]

#final recommender system    

def recommend_products(user_id, num_recommendations=10):
    user = User.query.get(user_id)
    if not user:
        return []

    recommendations = []

    # 1. Collaborative Filtering (User-Based)
    similar_users = get_similar_users(user_id)
    for similar_user_id in similar_users:
        recommendations.extend(get_user_purchased_products(similar_user_id))

    # 2. Collaborative Filtering (Item-Based)
    user_purchased_products = get_user_purchased_products(user_id)
    for product in user_purchased_products:
        recommendations.extend(get_similar_products(product))

    # 3. Content-Based Recommendations
    for product in user_purchased_products:
        recommendations.extend(get_content_based_recommendations(product))

    # 4. Popularity-Based Recommendations
    popular_products = get_most_popular_products()
    recommendations.extend(popular_products)

    # 5. Personalized Recommendations
    personalized_recommendations = get_personalized_recommendations(user)
    recommendations.extend(personalized_recommendations)

    # Deduplicate and limit to the number of recommendations required
    recommendations = list(set(recommendations))
    recommendations = recommendations[:num_recommendations]

    return recommendations


@bp.route('/api/track-product-event', methods=['POST'])
def track_product_event():
    try:
        data = request.json

        product_id = data.get('productId')
        event_type = data.get('eventType')
        timestamp = data.get('timestamp')

        if not product_id or not event_type or not timestamp:
            return jsonify({'error': 'Missing data in request'}), 400

        user_id = get_current_user_id()  # Determine user ID or default to 0

        if event_type == 'click':
            record_click_event(user_id, product_id, timestamp)
        elif event_type == 'view':
            record_view_event(user_id, product_id, timestamp)
        else:
            return jsonify({'error': 'Invalid event type'}), 400

        return jsonify({'message': 'Event tracked successfully'}), 200
    except Exception as e:
        app.logger.error(f"Error tracking event: {e}")
        return jsonify({'error': 'Server error'}), 500



def record_click_event(user_id, product_id, timestamp):
    try:
        new_click = ProductClick(user_id=user_id, product_id=product_id, timestamp=datetime.fromisoformat(timestamp))
        db.session.add(new_click)
        product = Product.query.get(product_id)
        if product:
            product.click_count += 1
        db.session.commit()
    except Exception as e:
        app.logger.error(f"Error recording click event: {e}")
        db.session.rollback()

def record_view_event(user_id, product_id, timestamp):
            try:
                new_view = ProductView(user_id=user_id, product_id=product_id, timestamp=datetime.fromisoformat(timestamp))
                db.session.add(new_view)
                product = Product.query.get(product_id)
                if product:
                    product.view_count += 1
                    db.session.commit()
            except Exception as e:
                # Handle exceptions appropriately
                print(f"Error recording view event: {e}")
                db.session.rollback()  # Rollback changes in case of an exception


def get_current_user_id():
    if current_user.is_authenticated:
        return current_user.id
    else:
        return 0  # Return 0 for guest users


