from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app.admin import admin_bp
from app.main.forms import AddProductCategoryForm, AddProductForm, ProductImageForm, AddProductForm, CheckoutForm,  RegistrationForm,  LoginForm, AddLocationForm, AddRoleForm, AddSupplierForm, AddNearestPlaceForm, AddArealineForm
from app.main.models import User, Role, Cart,  ProductCategory,  Product, Order, OrderItem, Location, Cart, Arealine, NearestPlace, Arealine, UserDeliveryInfo
from app import db
from flask import jsonify
from sqlalchemy import cast, Date, func
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from app import db, mail
from flask_mail import Message
from flask_migrate import Migrate
from flask_migrate import Migrate


# Helper function to handle database errors and redirects
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
 # Fetch product categories
        categories = ProductCategory.query.all()
        
        # Fetch sales data
        sales_data = fetch_sales_data()
        #labels = [datetime.strptime(data.order_date, '%Y-%m-%d').strftime('%Y-%m-%d') for data in sales_data]
        labels = [datetime.strptime(str(data.order_date), '%Y-%m-%d').strftime('%Y-%m-%d') for data in sales_data]

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

        return render_template('admin_dashboard.html', users=users, roles=roles, admin_data=admin_data, user_growth_chart_image=user_growth_chart_image, categories=categories)

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
    form = AddProductCategoryForm()

    if form.validate_on_submit():
        category = ProductCategory(name=form.name.data)
        db.session.add(category)
        db.session.commit()
        flash('Product category added successfully', 'success')

    categories = ProductCategory.query.all()

    return render_template('add_product_category.html', form=form, categories=categories)


# Add a new route to display products under a specific category
@admin_bp.route('/products_by_category/<int:category_id>')
def products_by_category(category_id):
    category = ProductCategory.query.get_or_404(category_id)
    products = Product.query.filter_by(category=category).all()
    return render_template('products_by_category.html', category=category, products=products)


@admin_bp.route('/add_location', methods=['GET', 'POST'])
@login_required
def add_location():
    def route():
        # Initialize forms for adding location, arealine, and nearest place
        form_location = AddLocationForm()
        form_arealine = AddArealineForm()
        form_nearest_place = AddNearestPlaceForm()

        # Fetch locations and arealines for dropdowns
        locations = Location.query.all()
        arealines = Arealine.query.all()

        # Set choices for location field in AddArealineForm
        form_arealine.location.choices = [(location.id, location.name) for location in locations]

        # Set choices for arealine field in AddNearestPlaceForm
        form_nearest_place.arealine.choices = [(arealine.id, arealine.name) for arealine in arealines]

        # Handle form submissions
        if form_location.validate_on_submit():
            existing_location = Location.query.filter_by(name=form_location.location_name.data).first()

            if existing_location:
                flash('Location already exists!', 'error')
            else:
                # Process Add Location Form
                location = Location(name=form_location.location_name.data)
                db.session.add(location)
                db.session.commit()
                flash('Location added successfully!', 'success')

        elif form_arealine.validate_on_submit():
            existing_arealine = Arealine.query.filter_by(name=form_arealine.name.data,
                                                         location_id=form_arealine.location.data).first()

            if existing_arealine:
                flash('Arealine already exists!', 'error')
            else:
                # Process Add Arealine Form
                arealine = Arealine(name=form_arealine.name.data,
                                    location_id=form_arealine.location.data)
                db.session.add(arealine)
                db.session.commit()
                flash('Arealine added successfully!', 'success')

        elif form_nearest_place.validate_on_submit():
            existing_nearest_place = NearestPlace.query.filter_by(name=form_nearest_place.name.data,
                                                                 arealine_id=form_nearest_place.arealine.data).first()

            if existing_nearest_place:
                flash('Nearest Place already exists!', 'error')
            else:
                # Process Add Nearest Place Form
                nearest_place = NearestPlace(name=form_nearest_place.name.data,
                                             arealine_id=form_nearest_place.arealine.data)
                db.session.add(nearest_place)
                db.session.commit()
                flash('Nearest Place added successfully!', 'success')

        # Render the template with the forms and data
        return render_template('add_location.html',
                               form_location=form_location,
                               form_arealine=form_arealine,
                               form_nearest_place=form_nearest_place,
                               locations=locations,
                               arealines=arealines)

    # Use helper function to handle database errors and redirects
    return handle_db_error_and_redirect(route)



@admin_bp.route('/get_locations', methods=['GET'])
def get_locations():
    locations = Location.query.all()
    locations_data = [{'id': location.id, 'name': location.name} for location in locations]
    return jsonify({'locations': locations_data})
  

@admin_bp.route('/get_arealines/<location_id>', methods=['GET'])
def get_arealines(location_id):
    location = Location.query.get(location_id)

    if not location:
        return jsonify({'error': 'Invalid location ID'}), 400

    arealines = [{'id': arealine.id, 'name': arealine.name} for arealine in location.arealines]
    
    return jsonify({'arealines': arealines})


    

@admin_bp.route('/get_nearest_places/<arealine_id>', methods=['GET'])
def get_nearest_places(arealine_id):
    arealine = Arealine.query.get(arealine_id)

    if not arealine:
        return jsonify({'error': 'Invalid arealine ID'}), 400

    nearest_places = [{'id': place.id, 'name': place.name} for place in arealine.nearest_places]

    return jsonify({'nearest_places': nearest_places})


@admin_bp.route('/view_order_details/<int:order_id>')
def view_order_details(order_id):
    def route():
        order = Order.query.get_or_404(order_id)
        return render_template('view_order_details.html', order=order)

    return handle_db_error_and_redirect(route)

@admin_bp.route('/confirm_order/<int:order_id>', methods=['POST'])
@login_required
def confirm_order(order_id):
    if not current_user.is_authenticated or (current_user.role and current_user.role.name != 'admin'):
        abort(403)

    order = Order.query.get_or_404(order_id)
    order.status = 'confirmed'
    db.session.commit()

    # Send confirmation email
    msg = Message('Order Confirmation', recipients=[order.user.email])
    msg.body = f"Dear {order.user.username},\n\n We're thrilled to inform you that your order #{order.id} has been successfully confirmed! 🎉. \n\n If you have any questions or need assistance with your order, feel free to reach out to our customer support team at support@nourishagroceries.com or by replying to this email.!\n\nThank you once again for choosing Nourisha Groceries. We truly appreciate your support!\nBest regards,\n\nThe Nourisha Team"
    mail.send(msg)

    flash('Order confirmed successfully!', 'success')
    return redirect(url_for('admin.view_orders'))
  
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

        sendmail(
            subject='Order Cancellation',
            recipients=[order.user.email],
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

def sendmail(subject, recipients, body):
    msg = Message(subject, recipients=recipients)
    msg.body = body
    mail.send(msg)