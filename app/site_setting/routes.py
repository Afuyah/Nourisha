from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.site_setting import site_bp
from app import db
from app.main.models import Offer
from app.main.forms import OfferForm
from flask_login import current_user, login_user, logout_user, login_required
from app.main.models import User



@site_bp.route('/offers', methods=['GET', 'POST'])
@login_required
def offers():
    form = OfferForm()

    if form.validate_on_submit():
        offer = Offer(
            title=form.title.data,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            active=form.active.data
        )
        db.session.add(offer)
        db.session.commit()
        flash('Offer created successfully!', 'success')
        return redirect(url_for('site.offers'))

    offers = Offer.query.all()
    return render_template('offers.html', form=form, offers=offers)

@site_bp.route('/edit_offer/<int:offer_id>', methods=['GET', 'POST'])
@login_required
def edit_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    form = OfferForm(obj=offer)

    if form.validate_on_submit():
        offer.title = form.title.data
        offer.description = form.description.data
        offer.start_date = form.start_date.data
        offer.end_date = form.end_date.data
        offer.active = form.active.data

        db.session.commit()
        flash('Offer updated successfully!', 'success')
        return redirect(url_for('site.offers'))

    return render_template('edit_offer.html', form=form, offer=offer)

@site_bp.route('/delete_offer/<int:offer_id>', methods=['POST'])
@login_required
def delete_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    db.session.delete(offer)
    db.session.commit()
    flash('Offer deleted successfully!', 'success')
    return redirect(url_for('site.offers'))

@site_bp.route('/home', methods=['GET', 'POST'])
def client_offers():
    offers = Offer.query.filter_by(active=True).all()
    return render_template('home.html', offers=offers)

