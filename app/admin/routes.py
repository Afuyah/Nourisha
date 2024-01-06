from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.admin import admin_bp
from app.main.forms import AddProductCategoryForm, AddProductForm, ProductImageForm, AddProductForm, CheckoutForm,  RegistrationForm, CustomerLocationForm, LoginForm, AddLocationForm, AddRoleForm, AddSupplierForm
from app.main.models import User, Role, Cart, Supplier, ProductImage,  ProductCategory,  Product, Order, OrderItem, Location, Cart
from app import db
from sqlalchemy import cast, Date, func
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.dates import DateFormatter
import matplotlib


matplotlib.use('agg')  # Use the 'agg' backend for a non-interactive environment




def handle_db_error_and_redirect(route):
    try:
        return route()
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Database error: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

def fetch_sales_data():
    # Fetch and process sales data from the database
    
    sales_data = db.session.query(
        func.date(Order.order_date).label('order_date'),
        func.sum(Order.total_price).label('total_sales')
    ).group_by(func.date(Order.order_date)).order_by(func.date(Order.order_date)).all()

    return sales_data

def create_sales_chart(labels, data):
    fig, ax = plt.subplots(figsize=(10, 6))

    date_objects = [datetime.strptime(label, '%Y-%m-%d') for label in labels]
    ax.plot(date_objects, data, marker='o', linestyle='-', color='b')

    ax.set_title('Sales Overview')
    ax.set_xlabel('Date')
    ax.set_ylabel('Total Sales ($)')
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    ax.tick_params(axis='x', rotation=45)

    return fig

def generate_chart_image(chart):
    image_stream = BytesIO()
    chart.savefig(image_stream, format='png')
    image_stream.seek(0)
    chart_image = base64.b64encode(image_stream.getvalue()).decode('utf-8')
    plt.close(chart)  # Close the provided chart, not 'fig'

    return f"data:image/png;base64,{chart_image}"




@admin_bp.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    def route():
        if current_user.role.name != 'admin':
            flash('You do not have permission to access the admin dashboard.', 'danger')
            return redirect(url_for('main.index'))

        # Fetch sales data
        sales_data = fetch_sales_data()
        labels = [datetime.strptime(data.order_date, '%Y-%m-%d').strftime('%Y-%m-%d') for data in sales_data]
        data = [float(data.total_sales) for data in sales_data]

        # Create sales chart
        sales_chart = create_sales_chart(labels, data)
        sales_chart_image = generate_chart_image(sales_chart)

        # Call the function to get top-selling products
        top_selling_products = db.session.query(
            Product,
            db.func.sum(OrderItem.quantity).label('total_quantity_sold'),
            db.func.sum(OrderItem.unit_price * OrderItem.quantity).label('total_revenue')
        ).join(OrderItem, Product.id == OrderItem.product_id).group_by(Product).order_by(db.desc('total_quantity_sold')).limit(3).all()

       

        admin_data = {
            'total_users': User.query.count(),
            'recent_users': User.query.order_by(User.registration_date.desc()).limit(5).all(),
            'sales_data': {'labels': labels, 'data': data},
            'total_products': Product.query.count(),
            'active_products': 0,  # You need to define how to calculate active products
            'out_of_stock': Product.query.filter(Product.quantity_in_stock == 0).count(),
            'recent_orders': Order.query.order_by(Order.order_date.desc()).limit(5).all(),
            'total_customers': User.query.count(),
            'new_customers_last_7_days': User.query.filter(User.registration_date >= (datetime.utcnow() - timedelta(days=7))).count(),
            'returning_customers': User.query.filter(User.registration_date < (datetime.utcnow() - timedelta(days=7))).count(),
             'top_selling_products': top_selling_products

        }

        users = User.query.all()
        roles = Role.query.all()

        if request.method == 'POST':
            flash('POST request received.', 'info')

        return render_template('admin_dashboard.html', users=users, roles=roles, admin_data=admin_data, sales_chart_image=sales_chart_image)

    return handle_db_error_and_redirect(route)



def get_top_selling_products():
    # Fetch top-selling products based on quantity sold
    top_selling_products = Product.query.order_by(Product.quantity_sold.desc()).limit(5).all()
    return top_selling_products



@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    def route():
        user = User.query.get_or_404(user_id)
        form = EditUserForm(obj=user)

        # Your existing logic for handling form submission goes here

        return render_template('edit_user.html', user=user, form=form)

    return handle_db_error_and_redirect(route)

@admin_bp.route('/admin/edit_role/<int:role_id>', methods=['GET', 'POST'])
@login_required
def edit_role(role_id):
    def route():
        role = Role.query.get_or_404(role_id)

        if request.method == 'POST':
            flash('Role updated successfully!', 'success')
            return redirect(url_for('admin.admin_dashboard'))

        return render_template('edit_role.html', role=role)

    return handle_db_error_and_redirect(route)

@admin_bp.route('/product_categories', methods=['GET', 'POST'])
@login_required
def product_categories():
    def route():
        form = AddProductCategoryForm()

        if form.validate_on_submit():
            category = ProductCategory(name=form.name.data)
            db.session.add(category)
            db.session.commit()
            flash('Product category added successfully', 'success')

        categories = ProductCategory.query.all()

        return render_template('add_product_category.html', form=form, categories=categories)

    return handle_db_error_and_redirect(route)

@admin_bp.route('/add_location', methods=['GET', 'POST'])
@login_required
def add_location():
    def route():
        form = AddLocationForm()

        if form.validate_on_submit():
            location = Location(
                location_name=form.location_name.data,
                arealine=form.arealine.data
            )

            db.session.add(location)
            db.session.commit()

            flash('Location added successfully!', 'success')

        locations = Location.query.all()

        return render_template('add_location.html', form=form, locations=locations)

    return handle_db_error_and_redirect(route)

@admin_bp.route('/view_order_details/<int:order_id>')
def view_order_details(order_id):
    def route():
        order = Order.query.get_or_404(order_id)
        return render_template('view_order_details.html', order=order)

    return handle_db_error_and_redirect(route)

@admin_bp.route('/confirm_order/<int:order_id>', methods=['POST'])
@login_required
def confirm_order(order_id):
    def route():
        if not current_user.is_authenticated or (current_user.role and current_user.role.name != 'admin'):
            abort(403)

        order = Order.query.get_or_404(order_id)
        order.status = 'confirmed'
        db.session.commit()

        flash('Order confirmed successfully!', 'success')
        return redirect(url_for('admin.view_orders'))

    return handle_db_error_and_redirect(route)

@admin_bp.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    def route():
        if not current_user.is_authenticated or (current_user.role and current_user.role.name != 'admin'):
            abort(403)

        order = Order.query.get_or_404(order_id)
        order.status = 'canceled'

        for order_item in order.order_items:
            product = order_item.product
            product.quantity_in_stock += order_item.quantity

        db.session.commit()

        flash('Order canceled successfully!', 'success')
        return redirect(url_for('admin.view_orders'))

    return handle_db_error_and_redirect(route)

@admin_bp.route('/view_orders', methods=['GET'])
def view_orders():
    def route():
        if not current_user.is_authenticated or (current_user.role and current_user.role.name != 'admin'):
            abort(403)

        orders = Order.query.all()
        return render_template('view_orders.html', orders=orders)

    return handle_db_error_and_redirect(route)



def fetch_daily_sales_data():
    try:
        # Fetch daily sales data from the database
        # Modify this query based on your data model
        daily_sales_query = (
            db.session.query(
                db.func.strftime("%Y-%m-%d", Order.order_date).label("date"),
                db.func.sum(Order.total_price).label("total_sales")
            )
            .filter(Order.status == 'confirmed')  # Filter only confirmed orders
            .group_by(db.func.strftime("%Y-%m-%d", Order.order_date))
            .order_by(db.func.strftime("%Y-%m-%d", Order.order_date))
        )

        daily_sales_data = daily_sales_query.all()

        # Convert the query result to a format suitable for display
        labels = [entry.date for entry in daily_sales_data]
        data = [entry.total_sales for entry in daily_sales_data]

        return {'labels': labels, 'data': data}

    except Exception as e:
        # Log the error (optional)
        current_app.logger.error(f"Error fetching daily sales data: {str(e)}")
        # Return an empty dictionary or None, depending on your preference
        return {'labels': [], 'data': []}


