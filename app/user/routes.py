from app.user import user_bp
from flask import render_template, abort, Blueprint,flash, redirect, url_for, request, jsonify, send_file, session,current_app
from flask_login import current_user, login_user, logout_user, login_required
from app.main.forms import EditUserForm 

@user_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@user_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditUserForm()

    if form.validate_on_submit():
        
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.name = form.name.data
        db.session.commit()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user.user.profile'))

    return render_template('edit_profile.html', form=form)