from flask import render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from app.admin import admin_bp
from app.main.models import User, Role
from app import db

@admin_bp.route('/admin', methods=['GET'])
@login_required
def admin_portal():
    if not current_user.is_admin():
        flash('You do not have access to the admin portal.', 'danger')
        return redirect(url_for('main.index'))

    users = User.query.all()
    roles = Role.query.all()

    return render_template('admin/admin_portal.html', users=users, roles=roles)
