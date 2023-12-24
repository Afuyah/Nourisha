from app import db
from flask import render_template, abort, Blueprint,flash, redirect, url_for, request, jsonify, send_file, session,current_app
from flask_login import current_user, login_user, logout_user, login_required
from app.main import bp
from app.main.forms import AddProductCategoryForm, AddProductForm, ProductImageForm, AddProductForm, CheckoutForm,  RegistrationForm, CustomerLocationForm, LoginForm, AddRoleForm, AddSupplierForm
from app.main.models import User, Role, Cart, Supplier, ProductImage,  ProductCategory,  Product
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import pdfcrowd
from werkzeug.utils import secure_filename
import os 
from sqlalchemy.orm.exc import NoResultFound
from app.cart.routes import cart_bp

@bp.route('/')
def index():
     return render_template('home.html', title='Home', product_listing_url=url_for('main.product_listing'))

@bp.route('/register', methods=['GET', 'POST'])
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

            flash('Registration successful!', 'success')
            return redirect(url_for('main.login'))

        except IntegrityError as e:
            db.session.rollback()
            flash('Email address is already registered. Please use Sign In.', 'danger')
            return redirect(url_for('main.register'))

    return render_template('register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Use email for login instead of phone number
        user = User.query.filter_by(phone=form.phone.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user)
            user.last_login_date = datetime.utcnow()
            user.last_login_ip = request.remote_addr
            db.session.commit()
            flash('Login successful!', 'success')

            # Redirect to the admin dashboard if the user has the 'admin' role
            if user.role and user.role.name == 'admin':
                return redirect(url_for('admin.admin_dashboard'))

            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password', 'danger')
    
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

@bp.route('/generate_pdf', methods=['GET'])
def generate_pdf():
    # Fetch all suppliers
    suppliers = Supplier.query.all()

    # Render HTML template to a string
    html = render_template('pdf_template.html', suppliers=suppliers)

    # Create a pdfcrowd client
    client = pdfcrowd.HtmlToPdfClient('bha', 'a84c5fe3acd8f81c3baa119f07962071')

    # Convert HTML to PDF
    pdf = client.convertString(html)

    # Save the PDF to a file
    with open('suppliers_table.pdf', 'wb') as f:
        f.write(pdf)

    # Return the PDF file for download
    return send_file('suppliers_table.pdf', as_attachment=True)


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
        return redirect(url_for('main.products'))

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
    # Fetch products from the database (adjust the query as needed)
    products = Product.query.all()
    quantity = 10 
    form = AddProductForm()
      # Render a template with the product data
    return render_template('product_listing.html', products=products, quantity=quantity, form=form)

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



@bp.route('/main/api/update', methods=['POST'])
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

        # Example response
        response_data = {
            'status': 'success',
            'message': 'Cart updated successfully',
            'data': {
                'productId': product_id,
                'action': action,
                # Include any other relevant data in the response
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

    # Commit changes to the database
    db.session.commit()

def get_authenticated_user_id():
    # Replace this with your actual user authentication logic
    # For now, return a placeholder user_id (you should implement this based on your authentication mechanism)
    return current_user.get_id()