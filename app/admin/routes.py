from flask import render_template, redirect, url_for, flash, request, current_app,abort
from flask_login import current_user, login_required
from app.main.forms import EditUserForm, AddLocationForm
from app.admin import admin_bp
from app.main.models import User, Role, Location , Order
from app import db
from datetime import datetime

@admin_bp.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    # Check if the current user has the 'admin' role
    if current_user.role.name != 'admin':
        flash('You do not have permission to access the admin dashboard.', 'danger')
        return redirect(url_for('main.index'))

    # Add logic for the admin dashboard here
    admin_data = {
        'total_users': User.query.count(),
        
        'recent_users': User.query.order_by(User.registration_date.desc()).limit(5).all()
        # Add more data or queries as needed for your admin dashboard
    }

    # Example queries to retrieve users and roles
    users = User.query.all()
    roles = Role.query.all()
    if request.method == 'POST':
        # Handle the POST request (if needed)
        flash('POST request received.', 'info')

    return render_template('admin_dashboard.html', users=users, roles=roles, admin_data=admin_data)


@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Retrieve the user from the database
    user = User.query.get_or_404(user_id)

    # Create an instance of your EditUserForm and populate it with user data
    form = EditUserForm(obj=user)

    # Your existing logic for handling form submission goes here

    return render_template('edit_user.html', user=user, form=form)


@admin_bp.route('/admin/edit_role/<int:role_id>', methods=['GET', 'POST'])
@login_required
def edit_role(role_id):
    # Your logic for editing a role goes here
    role = Role.query.get_or_404(role_id)

    if request.method == 'POST':
        # Handle the POST request (if needed)
        flash('Role updated successfully!', 'success')
        return redirect(url_for('admin.admin_dashboard'))

    # Render the template with the role data
    return render_template('edit_role.html', role=role)

@admin_bp.route('/product_categories', methods=['GET', 'POST'])
@login_required
def product_categories():
    form = ProductCategoryForm()

    if form.validate_on_submit():
        category = ProductCategory(name=form.name.data)
        db.session.add(category)
        db.session.commit()
        flash('Product category added successfully', 'success')
        return redirect(url_for('admin.product_categories'))

    categories = ProductCategory.query.all()
    return render_template('admin/product_categories.html', form=form, categories=categories)


@admin_bp.route('/add_location', methods=['GET', 'POST'])
@login_required
def add_location():
    form = AddLocationForm()

    if form.validate_on_submit():
        location = Location(
            location_name=form.location_name.data,
            arealine=form.arealine.data
        )

        db.session.add(location)
        db.session.commit()

        flash('Location added successfully!', 'success')
        return redirect(url_for('admin.add_location'))

    locations = Location.query.all()

    return render_template('add_location.html', form=form, locations=locations)

@admin_bp.route('/view_order_details/<int:order_id>')
def view_order_details(order_id):
    # Fetch the order details from the database
    order = Order.query.get_or_404(order_id)

    # Render the order details template with the order data
    return render_template('view_order_details.html', order=order)

@admin_bp.route('/confirm_order/<int:order_id>', methods=['POST'])
@login_required
def confirm_order(order_id):
    # Check if the current user is an admin
    if not current_user.is_authenticated or (current_user.role and current_user.role.name != 'admin'):
        abort(403)   # Forbidden, user is not an admin

    # Fetch the order from the database
    order = Order.query.get_or_404(order_id)

    # Confirm the order (change status to 'confirmed')
    order.status = 'confirmed'
    db.session.commit()

    flash('Order confirmed successfully!', 'success')
    return redirect(url_for('admin.view_orders'))

@admin_bp.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    # Check if the current user is an admin
    if not current_user.is_authenticated or (current_user.role and current_user.role.name != 'admin'):
        abort(403)

    # Fetch the order from the database
    order = Order.query.get_or_404(order_id)

    # Cancel the order (change status to 'canceled')
    order.status = 'canceled'

    # Return items to stock
    for order_item in order.order_items:
        product = order_item.product
        product.quantity_in_stock += order_item.quantity

    db.session.commit()

    flash('Order canceled successfully!', 'success')
    return redirect(url_for('admin.view_orders'))