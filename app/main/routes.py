from app import db, mail
from flask import render_template, abort, Blueprint,flash, redirect, url_for, request, jsonify, send_file, session,current_app
from flask_login import current_user, login_user, logout_user, login_required
from app.main import bp
from app.admin import admin_bp
from app.main.forms import AddProductCategoryForm, AddProductForm, ProductImageForm, AddProductForm, CheckoutForm,  RegistrationForm, CustomerLocationForm, LoginForm, AddRoleForm, AddSupplierForm
from app.main.models import User, Role, Cart, Supplier, ProductImage,  ProductCategory,  Product, Order, OrderItem, Location, Cart
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
import os 
from flask import Flask
from sqlalchemy.orm.exc import NoResultFound
from app.cart.routes import cart_bp
from .send_email import send_confirmation_email
from flask_mail import Message
import logging

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# Instantiate the URLSafeTimedSerializer with a secret key
serializer = URLSafeTimedSerializer('mysecretkey')
def send_email(to, subject, body):
    msg = Message(subject, recipients=[to])
    msg.body = body
    mail.send(msg)


@bp.route('/')
def index():
    user_authenticated = current_user.is_authenticated
    return render_template('home.html', title='Home', product_listing_url=url_for('main.product_listing'), user_authenticated=user_authenticated)


@bp.route('/register', methods=['POST', 'GET'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                phone=form.phone.data,
                name=form.name.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()

            # Now that the user is committed, generate the confirmation token
            token = generate_confirmation_token(user.id)
            
            # Send confirmation email
            send_confirmation_email(user, token)

            flash('Registration successful! Please check your email for confirmation.', 'success')
            return redirect(url_for('main.login'))

        except IntegrityError:
            db.session.rollback()
            flash('Email address is already registered. Please use Sign In.', 'danger')
            return redirect(url_for('main.register'))

    return render_template('register.html', form=form)

def generate_confirmation_token(user_id):
    return serializer.dumps(user_id)

def send_confirmation_email(user, token):
    confirm_url = url_for('main.confirm_email', token=token, _external=True)
    subject = 'Confirm Your Email Address'
    body = f"Thank you for Joining Naurisha Family. Please click the following link to confirm your email address: {confirm_url}"
    send_email(user.email, subject, body)

from sqlalchemy.orm.exc import NoResultFound

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
    except NoResultFound:
        flash('User not found. Please register again.', 'danger')
    except Exception as e:
        flash(f'Error confirming email: {str(e)}', 'danger')
        current_app.logger.error(f"Error confirming email: {e}")

    return redirect(url_for('main.login'))




@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'POST' and form.validate_on_submit():
        # Your login logic here
        phone_number = form.phone.data
        user = User.query.filter_by(phone=phone_number).first()

        if user and user.check_password(form.password.data):
            if user.confirmed:
                login_user(user, remember=True)
                user.last_login_date = datetime.utcnow()
                user.last_login_ip = request.remote_addr
                db.session.commit()
                flash('Login successful!', 'success')

                # Redirect to the admin dashboard if the user has the 'admin' role
                if user.role and user.role.name == 'admin':
                    return redirect(url_for('admin.admin_dashboard'))


                return redirect(url_for('main.index'))
            else:
                flash('Your account is not confirmed. Please check your email for the confirmation link.', 'warning')
        else:
            flash('Invalid phone number or password. Please check your credentials and try again.', 'danger')

    return render_template('login.html', form=form)


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

    return render_template('add_product_category.html', form=form, categories=categories)

@bp.route('/add_supplier', methods=['GET', 'POST'])
@login_required
def add_supplier():
    form = AddSupplierForm()

    if form.validate_on_submit():
        # Create a new supplier using the form data
        supplier = Supplier(
            supplier_id=form.supplier_id.data,
            name=form.name.data,
            contact_person=form.contact_person.data,
            contact_email=form.contact_email.data,
            contact_phone=form.contact_phone.data,
            address=form.address.data,
            city=form.city.data
        )

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
    image_form.product.choices = [(product.id, product.name) for product in Product.query.all()]
    form.supplier.choices = [(supplier.id, supplier.name) for supplier in Supplier.query.all()]
    form.category.choices = [(category.id, category.name) for category in ProductCategory.query.all()]

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
            date_added=form.date_added.data
        )

        # Add and commit the new product to the database
        db.session.add(product)
        db.session.commit()

        flash('Product added successfully!', 'success')
        return redirect(url_for('main.add_product'))

    # Fetch all products for display
    products = Product.query.all()

    return render_template('add_product.html', form=form, products=products,image_form=image_form )


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
    form.product.choices = [(product.id, product.name) for product in Product.query.all()]

    if form.validate_on_submit():
        # Handle image uploads and save links to the database
        product_id = form.product.data
        cover_image = form.cover_image.data
        image1 = form.image1.data
        image2 = form.image2.data
        image3 = form.image3.data

        # Save cover image
        cover_filename = save_image(cover_image)
        cover_image_entry = ProductImage(product_id=product_id, cover_image=cover_filename)
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

# Helper function to save uploaded image and return the filename
def save_image(image_data):
    # Implement your image-saving logic here (e.g., using Flask-Uploads)
    # This is a basic example assuming you have an 'uploads' folder
    # and you want to save images with unique filenames
    filename = generate_unique_filename(image_data.filename)
    image_data.save(os.path.join('app', 'static', 'uploads', filename))
    return filename

# Helper function to generate a unique filename
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

        return render_template('product_details.html', product=product, images=[images])  # Wrap images in a list

    except NoResultFound:
        # Handle the case where the product with the given ID is not found
        abort(404)

@bp.route('/product_listing')
def product_listing():
    # Fetch products from the database
    products = Product.query.all()

    # Calculate the total number of products
    total_products = len(products)

    # Calculate the number of active products (you need to define the criteria for "active")
    active_products = sum(1 for product in products if product.quantity_in_stock > 0)

    # Calculate the number of products that are out of stock
    out_of_stock = sum(1 for product in products if product.quantity_in_stock == 0)

    quantity = 10 
    form = AddProductForm()
    # Render a template with the product data
    return render_template('product_listing.html', products=products, total_products=total_products,
                           active_products=active_products, out_of_stock=out_of_stock, quantity=quantity, form=form)
