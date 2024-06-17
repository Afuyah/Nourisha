from datetime import datetime, timedelta
from flask import abort, flash, jsonify, redirect, render_template, request, url_for, Response, send_file, current_app
from flask_login import current_user, login_required
from flask_mail import Message
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from app import db, mail
from app.admin import admin_bp
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
import os
from io import StringIO
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.main.forms import (
    AddArealineForm,
    AddLocationForm,
    AddNearestPlaceForm,
    AddProductCategoryForm,
    DateSelectionForm,
    FulfillmentForm,
)
from app.main.models import (
    Arealine,
    Location,
    NearestPlace,
    Order,
    OrderItem,
    Product,
    ProductCategory,
    Role,
    User,
)


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
    labels = [data.order_date.strftime('%Y-%m-%d') for data in sales_data]
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
    
    # Example: Assuming you have a 'UserActivity' model with 'timestamp' and 'activity_type' fields
    user_activity_data = (
        db.session.query(UserActivity.timestamp, UserActivity.activity_type)
        .order_by(UserActivity.timestamp.desc())
        .limit(10)  # Adjust the limit as needed
        .all()
    )

    return user_activity_data


@admin_bp.route('/all_users')
def all_users():
    users = User.query.all()
    return render_template('system_users.html', users=users)



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
            'recent_orders': Order.query.order_by(Order.order_date.desc()).limit(3).all(),
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




@admin_bp.route('/data_visualization', methods=['GET', 'POST'])
@login_required
def data_visualization():
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
            'recent_orders': Order.query.order_by(Order.order_date.desc()).limit(3).all(),
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

        return render_template('system_analytics.html', users=users, roles=roles, admin_data=admin_data, user_growth_chart_image=user_growth_chart_image, categories=categories)

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







@admin_bp.route('/generate_pdf')
@login_required  # Ensure this route is protected
def generate_pdf():
    users = User.query.all()  # Fetch all users

    # Create a buffer to hold the PDF data
    pdf_buffer = BytesIO()
    pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter)

    # Sample styles for paragraphs and table
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    subtitle_style = ParagraphStyle('Subtitle', fontSize=14, spaceAfter=12, alignment=1)
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4BACC6")),  # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#D9EAD3")),  # Body background
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#D9EAD3"), colors.white]),  # Alternating rows
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ])

    # Adding a logo to the document
    elements = []
    logo_path = os.path.join(current_app.static_folder, 'logoford.png')  # Path to the logo file

    if os.path.exists(logo_path):  # Ensure the logo file exists
        logo = Image(logo_path, width=2.5 * inch, height=1 * inch)  # Adjust size as needed
        logo.hAlign = 'CENTER'  # Align the logo at the center
        elements.append(logo)
        elements.append(Spacer(1, 0.2 * inch))  # Add some space below the logo

    # Adding a title and other elements
    elements.append(Paragraph("User Report", title_style))
    elements.append(Spacer(1, 0.2 * inch))  # Add some space after the title
    elements.append(Paragraph("A detailed list of all users", subtitle_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Define table headers and data
    table_data = [['#', 'Username', 'Email', 'Phone', 'Name']]
    for user in users:
        table_data.append([
            str(user.id),
            user.username,
            user.email,
            user.phone,
            user.name
            
        ])

    # Create the table and apply styling
    table = Table(table_data, hAlign='LEFT', colWidths=[0.7 * inch, 1.2 * inch, 1.8 * inch, 1.2 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch, 1 * inch])
    table.setStyle(table_style)
    elements.append(table)

    # Footer with page number (added during the build process)
    def add_page_number(canvas, doc):
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(200 * mm, 10 * mm, text)  # Positioned 200 mm from the left, and 10 mm from the bottom

    # Build the PDF
    pdf.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)

    # Move the buffer's cursor to the beginning
    pdf_buffer.seek(0)

    # Return the PDF file as a response
    return send_file(
        pdf_buffer,
        as_attachment=True,  # Forces the browser to prompt a download
        download_name='nourisha_users.pdf',  # Name of the downloaded file
        mimetype='application/pdf'
    )




@admin_bp.route('/generate_csv')
def generate_csv():
    users = User.query.all()

    # Create an in-memory file-like object to write CSV data
    csv_data = StringIO()
    writer = csv.writer(csv_data)

    # Write the header row
    writer.writerow([ 'Username', 'Email', 'Phone', 'Name', 'Registration Date', 'Last Login Date', 'Last Login IP' ])

    # Write data rows
    for user in users:
        writer.writerow([
           
            user.username,
            user.email,
            user.phone,
            user.name,
            str(user.registration_date),
            str(user.last_login_date),
            user.last_login_ip,
            
        ])

    # Seek to the beginning of the StringIO buffer
    csv_data.seek(0)

    # Return the CSV data as a response
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=users.csv'}
    )


# View Orders by Date
@admin_bp.route('/view_orders_by_date', methods=['GET', 'POST'])
@login_required
def view_orders_by_date():
    form = DateSelectionForm()
    orders = None
    if form.validate_on_submit():
        selected_date = form.order_date.data
        start_date = datetime.combine(selected_date, datetime.min.time())
        end_date = datetime.combine(selected_date, datetime.max.time())
        orders = Order.query.filter(
            Order.order_date >= start_date,
            Order.order_date <= end_date
        ).all()
    return render_template('view_orders_by_date.html', form=form, orders=orders)

# Order Details
@admin_bp.route('/admin/order/<int:order_id>', methods=['GET'])
@login_required
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    form = FulfillmentForm()  # Create the form instance
    return render_template('order_details.html', order=order, form=form)

# Confirm Order

@admin_bp.route('/admin/confirm_order/<int:order_id>', methods=['POST'])
@login_required
def confirm_order(order_id):
    order = Order.query.get_or_404(order_id)
    form = request.form

    if order.status == 'pending':
        expected_delivery_date = form.get('expected_delivery_date')
        if expected_delivery_date:
            order.expected_delivery_date = datetime.strptime(expected_delivery_date, '%Y-%m-%d')
            order.status = 'confirmed'
            db.session.commit()
            flash('Order confirmed successfully.', 'success')
        else:
            flash('Expected delivery date is required to confirm the order.', 'danger')
    else:
        flash('Order cannot be confirmed. It may already be confirmed or in a different status.', 'danger')

    return redirect(url_for('admin.order_details', order_id=order_id))

# Fulfill Order route
@admin_bp.route('/admin/fulfill_order/<int:order_id>', methods=['POST'])
@login_required
def fulfill_order(order_id):
    order = Order.query.get_or_404(order_id)
    form = request.form

    if order.status == 'confirmed':
        selected_items = form.getlist('items')
        if selected_items:
            for item_id in selected_items:
                item = OrderItem.query.get_or_404(item_id)
                item.fulfillment_status = 'Fulfilled'
                product = item.product
                product.quantity_sold += item.quantity

            order.status = 'out for delivery'
            db.session.commit()
            flash('Selected items fulfilled successfully.', 'success')
        else:
            flash('No items selected for fulfillment.', 'warning')
    else:
        flash('Failed to fulfill order. Please ensure the order is confirmed.', 'danger')

    return redirect(url_for('admin.order_details', order_id=order_id))



@admin_bp.route('/admin/mark_delivered/<int:order_id>', methods=['POST'])
@login_required
def mark_delivered(order_id):
    order = Order.query.get_or_404(order_id)
    form = request.form

    if order.status == 'out for delivery':
        delivery_remarks = form.get('delivery_remarks')

        # Ensure delivery remarks are provided and not just whitespace
        if delivery_remarks and delivery_remarks.strip():
            order.status = 'delivered'
            order.delivery_remarks = delivery_remarks.strip()  # Save the delivery remarks
            db.session.commit()
            flash('Order marked as delivered successfully with remarks.', 'success')
        else:
            flash('Delivery remarks are required to mark the order as delivered.', 'warning')
    else:
        flash('Failed to mark as delivered. Please ensure the order is out for delivery.', 'danger')

    return redirect(url_for('admin.order_details', order_id=order_id))

# View Orders by Status
@admin_bp.route('/admin/orders/<status>', methods=['GET'])
@login_required
def view_orders_by_status(status):
    # List of valid statuses, including 'completed'
    valid_statuses = ['pending', 'confirmed', 'out for delivery', 'delivered', 'canceled', 'completed']

    # Check if the provided status is valid
    if status not in valid_statuses:
        flash('Invalid status provided.', 'danger')
        return redirect(url_for('admin.dashboard'))

    # Query orders by the given status
    orders = Order.query.filter_by(status=status).all()

    return render_template('view_orders_by_status.html', orders=orders, status=status)




# fetching orders by status
@admin_bp.route('/admin/api/orders/<status>', methods=['GET'])
@login_required
def api_get_orders_by_status(status):
    # Define valid statuses, including 'completed'
    valid_statuses = ['pending', 'confirmed', 'out for delivery', 'delivered', 'canceled', 'completed']

    # Validate the status
    if status not in valid_statuses:
        return jsonify({'error': 'Invalid status'}), 400

    try:
        # Base query
        query = Order.query.filter_by(status=status)

        # Apply filters
        order_id = request.args.get('order_id', type=int)
        if order_id:
            query = query.filter(Order.id == order_id)

        user_name = request.args.get('user_name', type=str)
        if user_name:
            query = query.join(User).filter(User.name.ilike(f'%{user_name}%'))

        order_date = request.args.get('order_date', type=str)
        if order_date:
            query = query.filter(db.func.date(Order.order_date) == order_date)

        # Apply sorting
        sort_by = request.args.get('sort_by', type=str)
        if sort_by == 'total_price':
            query = query.order_by(Order.total_price)
        elif sort_by == 'status':
            query = query.order_by(Order.status)
        else:
            query = query.order_by(Order.order_date)

        # Fetch orders
        orders = query.all()

        # Serialize the orders to JSON format
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'user': order.user.name,
                'order_date': order.order_date.strftime('%Y-%m-%d'),
                'total_price': order.total_price,
                'status': order.status,
                'expected_delivery_date': order.expected_delivery_date.strftime('%Y-%m-%d') if order.expected_delivery_date else 'N/A'
            })

        return jsonify(orders_data)

    except Exception as e:
        app.logger.error(f"Error fetching orders by status: {e}")
        return jsonify({'error': 'An error occurred while fetching orders.'}), 500



        

