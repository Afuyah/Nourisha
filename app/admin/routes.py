from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app.admin import admin_bp
from app.main.forms import AddProductCategoryForm, AddProductForm, ProductImageForm, AddProductForm, CheckoutForm,  RegistrationForm,  LoginForm, AddLocationForm, AddRoleForm, AddSupplierForm
from app.main.models import User, Role, Cart, Supplier, ProductImage,  ProductCategory,  Product, Order, OrderItem, Location, Cart
from app import db
from flask import jsonify
from sqlalchemy import cast, Date, func
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from app import db, mail
from flask_mail import Message



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


def create_sales_chart_data(labels, data):
    sales_chart_data = {
        'labels': labels,
        'datasets': [{
            'label': 'Total Sales',
            'data': data,
            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1,
        }],
    }

    return sales_chart_data

@admin_bp.route('/get_sales_chart_data', methods=['GET'])
@login_required
def get_sales_chart_data():
    if current_user.role.name != 'admin':
        return jsonify({'error': 'Permission denied'}), 403

    sales_data = fetch_sales_data()
    labels = [datetime.strptime(data.order_date, '%Y-%m-%d').strftime('%Y-%m-%d') for data in sales_data]
    data = [float(data.total_sales) for data in sales_data]

    sales_chart_data = {
        'labels': labels,
        'data': data,
    }

    return jsonify(sales_chart_data)

@admin_bp.route('/get_average_order_value_by_day')
@login_required
def get_average_order_value_by_day():
    # Calculate average order value by day of the week
    average_order_values = db.session.query(func.extract('dow', Order.order_date), func.avg(Order.total_price)).group_by(func.extract('dow', Order.order_date)).all()

    # Convert the result to a dictionary for easier JSON serialization
    result = {int(day): avg_value for day, avg_value in average_order_values}

    return jsonify(result)


def fetch_user_activity_timeline():
    # Fetch user activity data based on your application's logic
    # Example: Assuming you have a 'UserActivity' model with 'timestamp' and 'activity_type' fields
    user_activity_data = (
        db.session.query(UserActivity.timestamp, UserActivity.activity_type)
        .order_by(UserActivity.timestamp.desc())
        .limit(10)  # Adjust the limit as needed
        .all()
    )

    return user_activity_data

@admin_bp.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    def route():
        if current_user is None or not current_user.is_authenticated or current_user.role is None or current_user.role.name != 'admin':
          flash('You do not have permission to access the admin dashboard.', 'danger')
          return redirect(url_for('main.index'))


        # Fetch sales data
        sales_data = fetch_sales_data()
        labels = [datetime.strptime(data.order_date, '%Y-%m-%d').strftime('%Y-%m-%d') for data in sales_data]
        data = [float(data.total_sales) for data in sales_data]
        
        # Fetch user registrations for user growth chart
        user_registrations = User.query.with_entities(User.registration_date).all()

        # Process the data to get counts per month
        registrations_by_month = {}
        for user_registration in user_registrations:
            registration_date = user_registration.registration_date

            # Ensure registration_date is a datetime object
            if isinstance(registration_date, datetime):
                month_year = registration_date.strftime('%b %Y')
                registrations_by_month[month_year] = registrations_by_month.get(month_year, 0) + 1

        # Create lists for chart labels and data
        chart_labels = list(registrations_by_month.keys())
        chart_data = list(registrations_by_month.values())

        # Create user growth chart
        user_growth_chart = create_user_growth_chart(chart_labels, chart_data)
        user_growth_chart_image = generate_chart_image(user_growth_chart)

        # Call the function to get top-selling products
        top_selling_products = db.session.query(
            Product,
            db.func.sum(OrderItem.quantity).label('total_quantity_sold'),
            db.func.sum(OrderItem.unit_price * OrderItem.quantity).label('total_revenue')
        ).join(OrderItem, Product.id == OrderItem.product_id).group_by(Product).order_by(db.desc('total_quantity_sold')).limit(4).all()

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
            'top_selling_products': top_selling_products,
            'user_growth_data': {'labels': chart_labels, 'data': chart_data},
        }

        users = User.query.all()
        roles = Role.query.all()

        if request.method == 'POST':
            flash('POST request received.', 'info')

        return render_template('admin_dashboard.html', users=users, roles=roles, admin_data=admin_data, user_growth_chart_image=user_growth_chart_image)

    return handle_db_error_and_redirect(route)



def create_user_growth_chart(labels, data):
    # Create a user growth chart using Chart.js
    user_growth_chart = {
        'type': 'line',
        'data': {
            'labels': labels,
            'datasets': [{
                'label': 'User Growth',
                'data': data,
                'borderColor': '#5bc0de',  # Adjust color as needed
                'borderWidth': 2,
                'pointRadius': 5,
                'pointBackgroundColor': '#5bc0de',  # Adjust color as needed
                'fill': False,
            }],
        },
        'options': {
            'scales': {
                'y': {'beginAtZero': True},
            },
        },
    }

    return user_growth_chart
def generate_chart_image(chart_data):
    # Generate chart image using the appropriate method (e.g., Chart.js image generation library)
    # Implement the logic based on your chosen method
    # Return the image URL or data
    pass

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



def send_email(subject, recipient, body):
    msg = Message(subject, recipients=[recipient])
    msg.body = body
    mail.send(msg)


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
        send_email(
            subject='Order Confirmation',
            recipient=order.user.email,
            body=f"Dear {order.user.username},\n\nYour order with ID {order.id} has been confirmed. Thank you for shopping with us!\n\nSincerely,\nThe Nourisha Team"
        )
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

        send_email(
            subject='Order Cancellation',
            recipient=order.user.email,
            body=f"Dear {order.user.username},\n\nYour order with ID {order.id} has been canceled. If you have any questions, please contact our support team.\n\nSincerely,\nThe Nourisha Team"
        )

        flash('Order canceled successfully! Cancellation email sent to the user.', 'success')
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