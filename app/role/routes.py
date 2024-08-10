from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.main.models import Role, User
from app.main.forms import AddRoleForm, UserRoleForm

role_bp = Blueprint('role', __name__)

@role_bp.route('/roles', methods=['GET', 'POST'])
@login_required
def manage_roles():
    form = AddRoleForm()
    if form.validate_on_submit():
        if form.name.data.lower() == 'admin':
            flash('You cannot add a role named "admin".', 'danger')
            return redirect(url_for('role.manage_roles'))
        role = Role(name=form.name.data)
        db.session.add(role)
        db.session.commit()
        flash('Role added successfully.', 'success')
        return redirect(url_for('role.manage_roles'))

    roles = Role.query.all()
    users_with_roles = User.query.filter(User.role_id.isnot(None)).options(db.joinedload(User.role)).all()
    
    # Organize users by role
    users_by_role = {}
    for user in users_with_roles:
        role_name = user.role.name
        if role_name not in users_by_role:
            users_by_role[role_name] = []
        users_by_role[role_name].append(user)
    
    return render_template('manage_roles.html', form=form, roles=roles, users_by_role=users_by_role)



@role_bp.route('/assign-role', methods=['GET', 'POST'])
@login_required
def assign_role():
    form = UserRoleForm()
    form.user.choices = [(u.id, u.username) for u in User.query.all()]
    form.role.choices = [(r.id, r.name) for r in Role.query.all()]

    if form.validate_on_submit():
        user = User.query.get(form.user.data)
        role = Role.query.get(form.role.data)
        if user and role:
            if role.name.lower() == 'admin':
                flash('You cannot assign the "admin" role to any user.', 'danger')
                return redirect(url_for('role.assign_role'))
            user.role_id = form.role.data
            db.session.commit()
            flash('Role assigned successfully.', 'success')
            return redirect(url_for('role.manage_roles'))

    return render_template('assign_role.html', form=form)

@role_bp.route('/roles/edit/<int:role_id>', methods=['GET', 'POST'])
@login_required
def edit_role(role_id):
    role = Role.query.get_or_404(role_id)
    if role.name.lower() == 'admin':
        flash('You cannot edit the "admin" role.', 'danger')
        return redirect(url_for('role.manage_roles'))
    
    form = AddRoleForm(obj=role)  # Initialize the form with existing role data

    if form.validate_on_submit():
        form.populate_obj(role)  # Populate the role object with form data
        db.session.commit()
        flash('Role updated successfully!', 'success')
        return redirect(url_for('role.manage_roles'))

    return render_template('edit_role.html', form=form, role=role)

@role_bp.route('/roles/delete/<int:role_id>', methods=['POST'])
@login_required
def delete_role(role_id):
    role = Role.query.get_or_404(role_id)
    if role.name.lower() == 'admin':
        flash('You cannot delete the "admin" role.', 'danger')
        return redirect(url_for('role.manage_roles'))

    # Check if there are users assigned to this role
    users_with_role = User.query.filter_by(role_id=role_id).all()
    if users_with_role:
        flash('You cannot delete this role as there are users assigned to it.', 'danger')
        return redirect(url_for('role.manage_roles'))

    db.session.delete(role)
    db.session.commit()
    flash('Role deleted successfully!', 'success')
    return redirect(url_for('role.manage_roles'))

@role_bp.route('/permissions', methods=['GET', 'POST'])
@login_required
def manage_permissions():
    form = AddPermissionForm()
    if form.validate_on_submit():
        permission = Permission(name=form.name.data, description=form.description.data)
        db.session.add(permission)
        db.session.commit()
        flash('Permission added successfully.')
        return redirect(url_for('role.manage_permissions'))

    permissions = Permission.query.all()
    return render_template('manage_permissions.html', form=form, permissions=permissions)

@role_bp.route('/assign-permissions', methods=['GET', 'POST'])
@login_required
def assign_permissions():
    form = AssignPermissionForm()
    form.role.choices = [(role.id, role.name) for role in Role.query.all()]
    form.permissions.choices = [(permission.id, permission.name) for permission in Permission.query.all()]

    if form.validate_on_submit():
        role = Role.query.get(form.role.data)
        role.permissions = [Permission.query.get(permission_id) for permission_id in form.permissions.data]
        db.session.commit()
        flash('Permissions assigned successfully.')
        return redirect(url_for('role.manage_roles'))

    return render_template('assign_permissions.html', form=form)

@role_bp.route('/remove-role/<int:user_id>', methods=['POST'])
@login_required
def remove_role(user_id):
    user = User.query.get_or_404(user_id)
    
    # Ensure the current user has the authority to make this change
    if current_user.role.name.lower() == 'admin' and user.role.name.lower() != 'admin':
        user.role_id = None  # Set role_id to None or some default value
        db.session.commit()
        flash('User role removed successfully.', 'success')
    else:
        flash('You cannot remove the role of an admin or yourself.', 'danger')
    
    return redirect(url_for('role.manage_roles'))

@role_bp.route('/users-with-roles', methods=['GET'])
@login_required
def users_with_roles():
    # Fetch all users along with their roles
    users = User.query.all()
    return render_template('manage_roles.html.html', users=users)

