from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from app.main.forms import EditUserForm, AddLocationForm
from app.admin import admin_bp
from app.main.models import User, Role, Location  
from app import db

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
