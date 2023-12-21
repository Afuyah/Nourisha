from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from app.main.forms import EditUserForm
from app.admin import admin_bp
from app.main.models import User, Role  # Import the Role model

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