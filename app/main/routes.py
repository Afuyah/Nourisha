from app import db
from flask import render_template, flash, redirect, url_for, request, send_file
from flask_login import current_user, login_user, logout_user, login_required
from app.main import bp
from app.main.forms import RegistrationForm, LoginForm, AddRoleForm, AddSupplierForm
from app.main.forms import AddProductCategoryForm
from app.main.models import User, Role
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.main.models import ProductCategory
from app.main.models import Supplier
import pdfcrowd
from flask import render_template



@bp.route('/')
def index():
    return render_template('home.html', title='Home')

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

    # Populate choices for select fields
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

    return render_template('add_product.html', form=form, products=products)


# Additional routes for viewing, editing, and deleting products can be added here
# Example:
@bp.route('/view_product/<int:product_id>')
@login_required
def view_product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('view_product.html', product=product)