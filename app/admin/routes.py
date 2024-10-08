from datetime import datetime, timedelta
from flask import abort, flash, jsonify, redirect, render_template, request, url_for, Response, send_file, current_app as app
from flask_login import current_user, login_required
from flask_mail import Message
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from app import db, mail, socketio, admin_required
from app.admin import admin_bp
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from flask_login import user_logged_in, user_logged_out
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable, Flowable, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm, cm
import os
from functools import wraps
from reportlab.lib.pagesizes import letter



from reportlab.pdfgen import canvas
from app.main.forms import (
    AddArealineForm,
    AddLocationForm,
    
    AddProductCategoryForm,
    DateSelectionForm,
    FulfillmentForm,
    ShopForUserForm,
    EditProductCategoryForm,
    AddUserForm,
    
)
from app.main.models import (
    Arealine,
    Location,
   
    Order,
    OrderItem,
    Product,
    ProductCategory,
    Role,
    User,
    Cart,
    Purchase,
    Payment,
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
@admin_required
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
@admin_required
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
@admin_required
def all_users():
    users = User.query.all()
    form = AddUserForm()
    return render_template('system_users.html', users=users, form=form)



@admin_bp.route('/admin_dashboard', methods=['GET', 'POST'])
@admin_required
def admin_dashboard():
    def route():
        if current_user is None or not current_user.is_authenticated or current_user.role is None or current_user.role.name != 'admin':
          flash('You do not have permission to access the admin dashboard.', 'danger')
          return redirect(url_for('main.index'))
 
        return render_template('admin_dashboard.html')

    return handle_db_error_and_redirect(route)




@admin_bp.route('/data_visualization', methods=['GET', 'POST'])
@admin_required
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
@admin_required
def edit_user(user_id):
    def route():
        user = User.query.get_or_404(user_id)
        form = EditUserForm(obj=user)

        # Your existing logic for handling form submission goes here

        return render_template('edit_user.html', user=user, form=form)

    return handle_db_error_and_redirect(route)

@admin_bp.route('/admin/edit_role/<int:role_id>', methods=['GET', 'POST'])
@admin_required
def edit_role(role_id):
    def route():
        role = Role.query.get_or_404(role_id)

        if request.method == 'POST':
            flash('Role updated successfully!', 'success')
            return redirect(url_for('admin.admin_dashboard'))

        return render_template('edit_role.html', role=role)

    return handle_db_error_and_redirect(route)

@admin_bp.route('/product_categories', methods=['GET', 'POST'])
@admin_required
def product_categories():
    form = AddProductCategoryForm()
    edit_form = EditProductCategoryForm()

    if form.validate_on_submit():
        category = ProductCategory(name=form.name.data, tagline=form.tagline.data, description=form.description.data)
        db.session.add(category)
        db.session.commit()
        flash('Product category added successfully', 'success')
        return redirect(url_for('admin.product_categories'))

    categories = ProductCategory.query.all()
    return render_template('add_product_category.html', form=form, edit_form=edit_form, categories=categories)

@admin_bp.route('/edit_category/<int:category_id>', methods=['POST'])
@admin_required
def edit_category(category_id):
    edit_form = EditProductCategoryForm()
    category = ProductCategory.query.get_or_404(category_id)

    if edit_form.validate_on_submit():
        category.name = edit_form.name.data
        category.tagline = edit_form.tagline.data
        category.description = edit_form.description.data

        if edit_form.image.data:
            filename = secure_filename(edit_form.image.data.filename)
            image_path = os.path.join(current_app.root_path, 'static/uploads', filename)
            edit_form.image.data.save(image_path)
            category.image = filename

        db.session.commit()
        flash('Category updated successfully', 'success')

    return redirect(url_for('admin.product_categories'))


# Add a new route to display products under a specific category
@admin_bp.route('/products_by_category/<int:category_id>')
@admin_required
def products_by_category(category_id):
    category = ProductCategory.query.get_or_404(category_id)
    products = Product.query.filter_by(category=category).all()
    return render_template('products_by_category.html', category=category, products=products)

# Add Location Route
@admin_bp.route('/add_location', methods=['GET', 'POST'])
@admin_required
def add_location():
    def route():
        # Initialize forms for adding location and arealine
        form_location = AddLocationForm()
        form_arealine = AddArealineForm()

        # Fetch locations for dropdowns in AddArealineForm
        locations = Location.query.all()

        # Convert arealines query into list in the view to avoid issues
        for location in locations:
            location.arealines_list = list(location.arealines)

        # Set choices for location field in AddArealineForm
        form_arealine.location.choices = [(location.id, location.name) for location in locations]

        # Handle form submissions
        if form_location.validate_on_submit():
            existing_location = Location.query.filter_by(name=form_location.location_name.data).first()

            if existing_location:
                flash('Location already exists!', 'error')
            else:
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
                arealine = Arealine(name=form_arealine.name.data,
                                    location_id=form_arealine.location.data)
                db.session.add(arealine)
                db.session.commit()
                flash('Arealine added successfully!', 'success')

        # Render the template with the forms and data
        return render_template('add_location.html',
                               form_location=form_location,
                               form_arealine=form_arealine,
                               locations=locations)

    # Use helper function to handle database errors and redirects
    return handle_db_error_and_redirect(route)



# Endpoint to Fetch Locations
@admin_bp.route('/get_locations', methods=['GET'])
@login_required
def get_locations():
    try:
        locations = Location.query.all()
        locations_data = [{'id': location.id, 'name': location.name} for location in locations]
        return jsonify({'locations': locations_data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error fetching locations: {str(e)}'}), 500


# Endpoint to Fetch Arealines for a Specific Location
@admin_bp.route('/get_arealines/<int:location_id>', methods=['GET'])
@login_required
def get_arealines(location_id):
    try:
        location = Location.query.get(location_id)

        if not location:
            return jsonify({'status': 'error', 'message': 'Invalid location ID'}), 400

        # Use .all() to explicitly load the arealines if lazy-loaded
        arealines = [{'id': arealine.id, 'name': arealine.name} for arealine in location.arealines.all()]

        return jsonify({'arealines': arealines})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error fetching arealines: {str(e)}'}), 500

@admin_bp.route('/view_order_details/<int:order_id>')
@admin_required
def view_order_details(order_id):
    def route():
        order = Order.query.get_or_40704(order_id)
        return render_template('view_order_details.html', order=order)

    return handle_db_error_and_redirect(route)



@admin_bp.route('/cancel_order/<int:order_id>', methods=['POST'])
@admin_required
@admin_required
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
@admin_required
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



@admin_bp.route('/generate_allusers_pdf')
@admin_required
def generate_allusers_pdf():
    # Fetch all users
    users = User.query.all()
    form = AddUserForm()
    # Create a buffer to hold the PDF data
    pdf_buffer = BytesIO()
    pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=1*inch, bottomMargin=1*inch, leftMargin=1*inch, rightMargin=1*inch)

    # Sample styles for paragraphs and table
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        fontSize=18,
        leading=22,
        fontName='Helvetica-Bold',
        alignment=1,
        textColor=colors.HexColor("#003366"),
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        fontSize=12,
        leading=15,
        fontName='Helvetica',
        alignment=1,
        textColor=colors.HexColor("#666666"),
        spaceAfter=6
    )
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),  # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#E6F2FF")),  # Body background
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#E6F2FF"), colors.white]),  # Alternating rows
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ])

    # Elements to add to the PDF
    elements = []

    # Adding header with logo and title
    logo_path = os.path.join(current_app.static_folder, 'logoford.png')  # Path to the logo file
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2.5*inch, height=1*inch)
        elements.append(logo)

    # Add title and subtitle
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("<b>User Report</b>", title_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph("<i>A detailed list of all users</i>", subtitle_style))
    elements.append(Spacer(1, 0.4*inch))

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

    # Create the table with improved styling
    table = Table(table_data, hAlign='CENTRE', colWidths=[0.7*inch, 1.2*inch, 2.2*inch, 1.5*inch, 2.0*inch])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(PageBreak())

    # Add a border around each page
    def draw_page_border(canvas, doc):
        canvas.saveState()
        width, height = letter
        border_margin = 0.5 * cm
        canvas.setLineWidth(0.5)
        canvas.setStrokeColor(colors.HexColor("#003366"))
        canvas.rect(border_margin, border_margin, width - 2 * border_margin, height - 2 * border_margin)
        canvas.restoreState()

    # Add header and footer
    def add_header_footer(canvas, doc):
        canvas.saveState()
        width, height = letter
        border_margin = 0.5 * cm


        # Footer
        footer_text = f"Page {doc.page}"
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawRightString(width - border_margin, border_margin - 10, footer_text)
        canvas.restoreState()

    # Build the PDF with the new border and header/footer
    pdf.build(
        elements,
        onFirstPage=lambda c, d: (draw_page_border(c, d), add_header_footer(c, d)),
        onLaterPages=lambda c, d: (draw_page_border(c, d), add_header_footer(c, d))
    )

    # Move the buffer's cursor to the beginning
    pdf_buffer.seek(0)

    # Return the PDF file as a response
    return send_file(
        pdf_buffer,
        as_attachment=True,  # Forces the browser to prompt a download
        download_name='nourisha_users.pdf',  # Name of the downloaded file
        mimetype='application/pdf'
    )



# View Orders by Date
@admin_bp.route('/view_orders_by_date', methods=['GET', 'POST'])
@admin_required
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
        app.logger.info(f'Orders fetched for date: {selected_date}')
    return render_template('view_orders_by_date.html', form=form, orders=orders)


# Order Details
@admin_bp.route('/admin/order/<int:order_id>', methods=['GET'])
@admin_required
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    form = FulfillmentForm()
    app.logger.info(f'Viewing details for order ID: {order_id}')
    return render_template('order_details.html', order=order, form=form)


# Confirm Order

@admin_bp.route('/admin/confirm_order/<int:order_id>', methods=['POST'])
@admin_required
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
            app.logger.info(f'Order ID {order_id} confirmed with delivery date {expected_delivery_date}')
        else:
            flash('Expected delivery date is required to confirm the order.', 'danger')
    else:
        flash('Order cannot be confirmed. It may already be confirmed or in a different status.', 'danger')

    return redirect(url_for('admin.order_details', order_id=order_id))


@admin_bp.route('/admin/fulfill_order/<int:order_id>', methods=['POST'])
@admin_required
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

            order.status = 'disparched'
            db.session.commit()
            flash('Selected items fulfilled successfully.', 'success')
            app.logger.info(f'Order ID {order_id} items fulfilled.')
        else:
            flash('No items selected for fulfillment.', 'warning')
    else:
        flash('Failed to fulfill order. Please ensure the order is confirmed.', 'danger')

    return redirect(url_for('admin.order_details', order_id=order_id))




@admin_bp.route('/admin/mark_delivered/<int:order_id>', methods=['POST'])
@admin_required
def mark_delivered(order_id):
    order = Order.query.get_or_404(order_id)
    form = request.form

    if order.status == 'disparched':
        delivery_remarks = form.get('delivery_remarks')

        if delivery_remarks and delivery_remarks.strip():
            order.status = 'delivered'
            order.delivery_remarks = delivery_remarks.strip()
            db.session.commit()
            flash('Order marked as delivered successfully with remarks.', 'success')
            app.logger.info(f'Order ID {order_id} marked as delivered with remarks: {delivery_remarks}')
        else:
            flash('Delivery remarks are required to mark the order as delivered.', 'warning')
    else:
        flash('Failed to mark as delivered. Please ensure the order is out for delivery.', 'danger')

    return redirect(url_for('admin.order_details', order_id=order_id))



@admin_bp.route('/admin/purchase', methods=['GET', 'POST'])
@admin_required
def admin_purchase():
    selected_date = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))

    items_available = db.session.query(OrderItem) \
        .join(Order, OrderItem.order_id == Order.id) \
        .join(Product, OrderItem.product_id == Product.id) \
        .join(User, Order.user_id == User.id) \
        .filter(OrderItem.purchase_status != 'Bought', db.func.date(Order.order_date) == selected_date) \
        .order_by(Order.id.desc()).all()

    items_bought = db.session.query(OrderItem) \
        .join(Order, OrderItem.order_id == Order.id) \
        .join(Product, OrderItem.product_id == Product.id) \
        .join(User, OrderItem.bought_by_admin_id == User.id) \
        .filter(OrderItem.purchase_status == 'Bought', db.func.date(Order.order_date) == selected_date) \
        .order_by(Order.id.desc()).all()

    app.logger.info(f'Admin purchase view for date: {selected_date}')
    return render_template('purchasing.html', items_available=items_available, items_bought=items_bought, selected_date=selected_date)


@admin_bp.route('/purchase/update', methods=['POST'])
@admin_required
def admin_purchase_update():
    data = request.json
    item_id = data.get('item_id')
    purchase_price = data.get('purchase_price')
    admin_id = current_user.id

    item = OrderItem.query.get_or_404(item_id)

    quantity_bought = item.quantity
    amount_paid = purchase_price * quantity_bought

    new_purchase = Purchase(
        order_item_id=item_id,
        user_id=admin_id,
        unit_price_bought=purchase_price,
        quantity_bought=quantity_bought,
        amount_paid=amount_paid
    )
    db.session.add(new_purchase)

    item.purchase_price = purchase_price
    item.bought_by_admin_id = admin_id
    item.purchase_status = 'Bought'
    db.session.commit()

    app.logger.info(f'Purchase updated for item ID {item_id} by admin ID {admin_id}')
    return jsonify({
        "status": "success",
        "item_id": item_id,
        "purchase_price": purchase_price,
        "admin_id": admin_id,
        "purchase_status": 'Bought'
    })



# View Orders by Status
@admin_bp.route('/admin/orders/<status>', methods=['GET'])
@admin_required
def view_orders_by_status(status):
    valid_statuses = ['pending', 'confirmed', 'out for delivery', 'delivered', 'canceled', 'completed']

    if status not in valid_statuses:
        flash('Invalid status provided.', 'danger')
        return redirect(url_for('admin.dashboard'))

    orders = Order.query.filter_by(status=status).all()

    status_counts = {
        'pending': len([order for order in orders if order.status == 'pending']),
        'confirmed': len([order for order in orders if order.status == 'confirmed']),
        'out for delivery': len([order for order in orders if order.status == 'out for delivery']),
        'delivered': len([order for order in orders if order.status == 'delivered']),
        'canceled': len([order for order in orders if order.status == 'canceled']),
        'completed': len([order for order in orders if order.status == 'completed'])
    }

    app.logger.info(f'Viewing orders by status: {status}')
    return render_template('view_orders_by_status.html', orders=orders, status=status, status_counts=status_counts)





# fetching orders by status
@admin_bp.route('/admin/api/orders/<status>', methods=['GET'])
@admin_required
def api_get_orders_by_status(status):
    valid_statuses = ['pending', 'confirmed', 'disparched', 'delivered', 'canceled', 'completed']

    if status not in valid_statuses:
        return jsonify({'error': 'Invalid status'}), 400

    try:
        query = Order.query.filter_by(status=status)

        order_id = request.args.get('order_id', type=int)
        if order_id:
            query = query.filter(Order.id == order_id)

        user_name = request.args.get('user_name', type=str)
        if user_name:
            query = query.join(User).filter(User.name.ilike(f'%{user_name}%'))

        order_date = request.args.get('order_date', type=str)
        if order_date:
            query = query.filter(db.func.date(Order.order_date) == order_date)

        sort_by = request.args.get('sort_by', type=str)
        if sort_by == 'total_price':
            query = query.order_by(Order.total_price)
        elif sort_by == 'status':
            query = query.order_by(Order.status)
        else:
            query = query.order_by(Order.order_date)

        orders = query.all()

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

        app.logger.info(f'API: Fetched orders by status: {status}')
        return jsonify(orders_data)

    except Exception as e:
        app.logger.error(f"Error fetching orders by status: {e}")
        return jsonify({'error': 'An error occurred while fetching orders.'}), 500



@admin_bp.route('/order/<int:order_id>/generate_invoice')
@admin_required
def generate_invoice(order_id):
    order = Order.query.get_or_404(order_id)
    fulfilled_items = [item for item in order.order_items if item.fulfillment_status == 'Fulfilled']

    if not fulfilled_items:
        flash('No fulfilled items to generate an invoice.', 'warning')
        return redirect(url_for('admin.order_details', order_id=order_id))

    subtotal = sum(item.total_price for item in fulfilled_items)
    shipping_fee = 200
    total_price = subtotal + shipping_fee

    pdf_buffer = generate_invoice_pdf(order, fulfilled_items, subtotal, shipping_fee, total_price)

    return send_file(pdf_buffer, as_attachment=True, download_name=f'Invoice_{order.id}.pdf', mimetype='application/pdf')



def generate_invoice_pdf(order, fulfilled_items, subtotal, shipping_fee, total_price):
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []

    styles = getSampleStyleSheet()

    # Define styles for various text elements
    company_name_style = ParagraphStyle(
        'CompanyName',
        fontSize=18,
        leading=22,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor("#2E7D32"),
        alignment=TA_LEFT
    )
    header_info_style = ParagraphStyle(
        'HeaderInfo',
        fontSize=8,
        leading=10,
        fontName='Helvetica',
        textColor=colors.HexColor("#333333"),
        alignment=TA_LEFT
    )
    tagline_style = ParagraphStyle(
        'Tagline',
        fontSize=10,
        leading=12,
        fontName='Helvetica-Oblique',
        textColor=colors.HexColor("#388E3C"),
        alignment=TA_LEFT
    )
    title_style = ParagraphStyle(
        'Title',
        fontSize=14,
        leading=20,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        textColor=colors.HexColor("#003366"),
        spaceAfter=10
    )
    subheader_style = ParagraphStyle(
        'SubHeader',
        fontSize=10,
        leading=12,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor("#003366"),
        spaceAfter=6
    )
    bold_style = ParagraphStyle(
        'Bold',
        fontSize=10,
        fontName='Helvetica-Bold'
    )
    footer_style = ParagraphStyle(
        'Footer',
        fontSize=10,
        fontName='Helvetica-Oblique',
        alignment=TA_CENTER,
        textColor=colors.HexColor("#4CAF50"),
        spaceAfter=8
    )
    normal_style = styles['Normal']
    normal_style.spaceAfter = 4

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#00539C")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#F0F4F8"), colors.white]),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ])

    # Header with logo and company information
    logo_path = os.path.join(app.static_folder, 'logoford.png')
    logo = Image(logo_path, width=1.2*inch, height=0.6*inch) if os.path.exists(logo_path) else None

    company_info = [
        [logo if logo else "",
         Paragraph("Nourisha Groceries", company_name_style),
         Paragraph("Fidel Odinga Rd, Mombasa, Kenya<br/>Phone: +254 707 632230<br/>Email: info@nourishagroceries.com", header_info_style)]
    ]

    company_info_table = Table(company_info, colWidths=[1.5*inch, 2.5*inch, 3*inch])
    elements.append(company_info_table)
    elements.append(Spacer(1, 0.05*inch))  # Reduced spacing

    # Add a horizontal line below the header
    elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor("#CCCCCC"), spaceBefore=0.1*inch, spaceAfter=0.1*inch))

    # Invoice title
    elements.append(Paragraph("Invoice", title_style))
    elements.append(Spacer(1, 0.05*inch))  # Reduced spacing

    # Invoice info and customer info side by side
    invoice_info = [
        [Paragraph("Invoice Number:", bold_style), f"INV-{order.id}"],
        [Paragraph("Invoice Date:", bold_style), order.order_date.strftime('%Y-%m-%d')],
        [Paragraph("Order ID:", bold_style), str(order.id)]
    ]

    customer_info = [
        [Paragraph("Customer Name:", bold_style), order.user.name],
        [Paragraph("Phone:", bold_style), order.user.phone],
        
    ]

    invoice_and_customer_info = Table([
        [
            Table(invoice_info, colWidths=[2*inch, 2.5*inch]),
            Table(customer_info, colWidths=[2*inch, 2.5*inch])
        ]
    ])
    elements.append(invoice_and_customer_info)
    elements.append(Spacer(1, 0.1*inch))  



    # Items purchased
    elements.append(Paragraph("Items Purchased", subheader_style))
    invoice_data = [
        [Paragraph("#", bold_style), Paragraph("Item Description", bold_style), Paragraph("Quantity", bold_style), Paragraph("Unit Price", bold_style), Paragraph("Total", bold_style)]
    ]

    item_counter = 1
    for item in fulfilled_items:
        invoice_data.append([
            str(item_counter),
            item.product.brand,
            str(item.quantity),
            f"Ksh {item.unit_price:.2f}",
            f"Ksh {item.total_price:.2f}"
        ])
        item_counter += 1

    # Adding summary
    invoice_data.append(["", "", "", "", ""])  # Empty row for spacing

    # Totals
    summary_data = [
        ["", "", Paragraph("Subtotal:", bold_style), f"Ksh {subtotal:.2f}"],
        ["", "", Paragraph("Shipping:", bold_style), f"Ksh {shipping_fee:.2f}"],
        ["", "", Paragraph("Tax:", bold_style),  0.00],
        ["", "", Paragraph("Total:", title_style), Paragraph(f"{total_price:.2f}", title_style)]
    ]

    # Apply the new table style without borders
    combined_table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#00539C")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#F0F4F8"), colors.white]),
    ])

    # Combine items table and summary table
    combined_table_data = invoice_data + summary_data
    combined_table = Table(combined_table_data, colWidths=[0.5*inch, 3.5*inch, 1*inch, 1*inch, 1*inch])
    combined_table.setStyle(combined_table_style)
    elements.append(combined_table)
    elements.append(Spacer(1, 0.3*inch))  # Reduced spacing

    # Footer
    elements.append(Paragraph("Thank you for your business!", normal_style))
    elements.append(Spacer(1, 0.2*inch))  # Reduced spacing

    # Add the company tagline at the footer
    elements.append(Paragraph("Promoting Healthy Living Through Healthy Eating", footer_style))

    pdf.build(elements)

    buffer.seek(0)
    return buffer
    return buffer
    


# Route to add a new user
@admin_bp.route('/admin/add_user', methods=['GET', 'POST'])
@admin_required
def add_user():
    form = AddUserForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.phone.data)
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            phone=form.phone.data,
            name=form.name.data,
            confirmed=True,
            password_hash=hashed_password,
            registration_date=datetime.utcnow()
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully!', 'success')
            return redirect(url_for('admin.admin_shop_for_user', user_id=new_user.id))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error adding user: {str(e)}')
            flash('Error adding user. Please try again.', 'danger')

    return render_template('system_users.html', form=form)

# Route to shop for a user
@admin_bp.route('/admin/shop_for_user', methods=['GET', 'POST'])
@admin_required
def admin_shop_for_user():
    form = ShopForUserForm()
    users = User.query.all()
    form.user.choices = [(user.id, user.username) for user in users]
    categories = ProductCategory.query.all()

    if form.validate_on_submit():
        user_id = form.user.data
        product_id = form.product.data
        quantity = form.quantity.data
        custom_description = form.custom_description.data

        product = Product.query.get(product_id)
        if not product:
            flash('Product not found!', 'error')
            return redirect(url_for('admin.admin_shop_for_user'))

        user = User.query.get(user_id)
        if not user:
            flash('User not found!', 'error')
            return redirect(url_for('admin.admin_shop_for_user'))

        unit_price = product.unit_price

        new_order_item = OrderItem(
            order_id=None,
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            custom_description=custom_description
        )
        db.session.add(new_order_item)
        db.session.commit()
        flash('Item added to order!', 'success')

    return render_template('admin_shop_for_user.html', form=form, users=users, categories=categories)

# Route to get products by category
@admin_bp.route('/admin/get_products')
@admin_required
def get_products():
    category_id = request.args.get('category_id')
    if category_id:
        products = Product.query.filter_by(category_id=category_id).all()
        product_list = [{'id': product.id, 'name': product.name, 'brand': product.brand, 'unit_price': product.unit_price} for product in products]
        return jsonify({'products': product_list})
    return jsonify({'products': []})

# Route to get items in the user's cart
@admin_bp.route('/admin/get_user_cart')
@admin_required
def get_user_cart():
    user_id = request.args.get('user_id')
    if user_id:
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        cart_data = []
        total_price = 0.0

        for item in cart_items:
            product = Product.query.get(item.product_id)
            if product:
                subtotal = item.quantity * product.unit_price
                cart_data.append({
                    'product_id': item.product_id,
                    'product_brand': product.brand,
                    'product_name': product.name,
                    'unit_price': product.unit_price,
                    'quantity': item.quantity,
                    'subtotal': subtotal,
                    'custom_description': item.custom_description
                })
                total_price += subtotal

        return jsonify({
            'cart_items': cart_data,
            'total_price': total_price
        }), 200
    return jsonify({'cart_items': []}), 400

# Route to add an item to the cart
@admin_bp.route('/admin/add_to_cart', methods=['POST'])
@admin_required
def add_to_cart():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    custom_description = data.get('custom_description')

    if not all([user_id, product_id, quantity]):
        return jsonify({'status': 'error', 'message': 'Incomplete data provided'}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'status': 'error', 'message': 'Product not found'}), 404

    existing_cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    if existing_cart_item:
        return jsonify({'status': 'error', 'message': 'Product already exists in the cart'}), 400

    try:
        new_cart_item = Cart(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            custom_description=custom_description
        )
        db.session.add(new_cart_item)
        db.session.commit()
        flash('Item added to cart successfully!', 'success')
        return jsonify({'status': 'success'}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Failed to add item to cart: {str(e)}')
        return jsonify({'status': 'error', 'message': 'Failed to add item to cart'}), 500

# Route to place an order for a user
@admin_bp.route('/admin/place_order_for_user', methods=['POST'])
@admin_required
def place_order_for_user():
    if current_user.role.name != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    cart_items = Cart.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({'message': 'No items in the cart for the user'}), 400

    total_price = calculate_total_price(cart_items)
    additional_services = 0
    shipping_fee = 200
    total_price += additional_services + shipping_fee

    location_id = data.get('location_id', 1)
    arealine_id = data.get('arealine_id', 1)
    nearest_place_id = data.get('nearest_place_id', 1)
    address_line = data.get('address_line', 'Call Client')
    if not address_line:
        return jsonify({'message': 'Address line is required'}), 400

    order = Order(
        user_id=user_id,
        status='pending',
        order_date=datetime.utcnow(),
        total_price=total_price,
        location_id=location_id,
        arealine_id=arealine_id,
        nearest_place_id=nearest_place_id,
        address_line=address_line,
        additional_info=data.get('additional_info'),
        payment_method=data.get('payment_method', 'pay on delivery'),
        phone_number=data.get('phone_number'),
        custom_description=data.get('custom_description')
    )

    try:
        db.session.add(order)
        db.session.commit()

        for cart_item in cart_items:
            product = cart_item.product
            if product:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=cart_item.quantity,
                    unit_price=product.unit_price,
                    custom_description=cart_item.custom_description
                )
                db.session.add(order_item)

        db.session.commit()
        clear_cart_for_user(user_id)

        order_data = {
            'order_id': order.id,
            'user_id': order.user_id,
            'order_date': order.order_date.strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'total_price': order.total_price,
            'additional_services': additional_services,
            'shipping_fee': shipping_fee,
            'order_items': [{
                'product_name': item.product.name,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'subtotal': item.quantity * item.unit_price,
                'custom_description': item.custom_description
            } for item in order.order_items]
        }

        return jsonify({'message': 'Order placed successfully!', 'order': order_data}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Failed to place order: {str(e)}')
        return jsonify({'message': 'Failed to place order'}), 500

# Route to complete an order
@admin_bp.route('/admin/complete_order/<int:order_id>', methods=['POST'])
@admin_required
def complete_order(order_id):
    if current_user.role.name != 'admin':
        flash('Unauthorized access!', 'error')
        return redirect(url_for('admin.some_redirect_route'))

    order = Order.query.get(order_id)
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('admin.some_redirect_route'))

    try:
        order.status = 'completed'
        db.session.commit()
        flash('Order completed successfully!', 'success')
        return redirect(url_for('admin.order_summary', order_id=order_id))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Failed to complete order {order_id}: {str(e)}')
        flash('Failed to complete order. Please try again.', 'danger')
        return redirect(url_for('admin.order_summary', order_id=order_id))


def calculate_total_price(cart_items):
    total = 0.0
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if product:
            total += item.quantity * product.unit_price
    return total


# Route to clear cart for a user
def clear_cart_for_user(user_id):
    try:
        Cart.query.filter_by(user_id=user_id).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error clearing cart for user {user_id}: {str(e)}')

# Route to remove an item from the cart
@admin_bp.route('/admin/remove_from_cart', methods=['POST'])
@admin_required
def remove_from_cart():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')

    if not user_id or not product_id:
        app.logger.error(f'Missing parameters: user_id={user_id}, product_id={product_id}')
        return jsonify({'message': 'User ID and Product ID are required'}), 400

    if current_user.role.name != 'admin':
        app.logger.warning(f'Unauthorized access attempt: user_id={user_id}, product_id={product_id}')
        return jsonify({'message': 'Unauthorized'}), 403

    cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

    if not cart_item:
        app.logger.info(f'Cart item not found: user_id={user_id}, product_id={product_id}')
        return jsonify({'message': 'Item not found in the cart'}), 404

    try:
        db.session.delete(cart_item)
        db.session.commit()
        app.logger.info(f'Item removed from cart: user_id={user_id}, product_id={product_id}')
        return jsonify({'message': 'Item removed from the cart successfully'}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error removing item from cart: {str(e)}')
        return jsonify({'message': f'Failed to remove item: {str(e)}'}), 500

# Route to get order details
@admin_bp.route('/admin/order_summary/<int:order_id>')
@admin_required
def order_summary(order_id):
    order = Order.query.get(order_id)
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('admin.some_redirect_route'))

    order_items = OrderItem.query.filter_by(order_id=order_id).all()
    return render_template('order_summary.html', order=order, order_items=order_items) 


@admin_bp.route('/user_accounts_info')
@login_required
def user_accounts_info():
    if current_user.role.name != 'admin':
        flash('Unauthorized access!', 'error')
        return redirect(url_for('main.product_listing'))
    return render_template('user_accounts_info.html')




@admin_bp.route('/get_users')
@login_required
def get_users():
    users = User.query.all()
    users_list = [{'id': user.id, 'name': user.name} for user in users]
    return jsonify(users_list)



@admin_bp.route('/get_user_info/<int:user_id>')
@login_required
def get_user_info(user_id):
    user = User.query.get_or_404(user_id)
    
    # Fetch the orders for the user
    orders = Order.query.filter_by(user_id=user_id).all()
    
    # Collect all payments associated with these orders
    payments = [payment for order in orders for payment in order.payments]

    # Calculate total amount due from all orders
    total_amount_due = sum(order.total_price for order in orders)
    
    # Calculate total amount paid from all payments
    total_amount_paid = sum(payment.amount_paid for payment in payments)
    
    # Calculate outstanding balance
    outstanding_balance = total_amount_due - total_amount_paid

    # Calculate purchase frequency
    purchase_frequency = len(orders) / 7  # Example: per week (this should be adjusted based on actual logic)

    # Logic to get most bought items
    item_counts = {}
    for order in orders:
        for item in order.order_items:
            if item.product.name in item_counts:
                item_counts[item.product.name] += item.quantity
            else:
                item_counts[item.product.name] = item.quantity
    most_bought_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    user_info = {
        'name': user.name,
        'phone': user.phone,
        'email': user.email,
       
        'outstanding_balance': outstanding_balance,
        'orders': [{'id': order.id, 'order_number': order.id, 'amount': order.total_price} for order in orders],
        'purchase_frequency': purchase_frequency,
        'last_login_date': user.last_login_date,
        'most_bought_items': [{'name': item[0], 'quantity': item[1]} for item in most_bought_items]
    }
    return jsonify(user_info)


@admin_bp.route('/get_order_details/<int:order_id>')
@login_required
def get_order_details(order_id):
    order = Order.query.get_or_404(order_id)
    order_details = {
        'order_number': order.order_number,
        'products': [{'name': item.product.name, 'quantity': item.quantity, 'price': item.price} for item in order.order_items]
    }
    return jsonify(order_details)
