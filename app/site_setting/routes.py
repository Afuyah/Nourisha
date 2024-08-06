from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
import os
from app import db, admin_required
from app.main.models import Offer, AboutUs, BlogPost, ContactMessage, Promotion, ProductPromotion, Product
from app.main.forms import OfferForm, AboutUsForm, BlogPostForm, ContactForm, PromotionForm, TagProductsForm

site_bp = Blueprint('site', __name__)

@site_bp.route('/offers', methods=['GET', 'POST'])
@admin_required
def offers():
    form = OfferForm()

    if form.validate_on_submit():
        filename = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            image_path = os.path.join(current_app.root_path, 'static/uploads', filename)
            form.image.data.save(image_path)

        offer = Offer(
            title=form.title.data,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            active=form.active.data,
            image=filename
        )
        db.session.add(offer)
        db.session.commit()
        flash('Offer created successfully!', 'success')
        return redirect(url_for('site.offers'))

    offers = Offer.query.all()
    return render_template('offers.html', form=form, offers=offers)

@site_bp.route('/edit_offer/<int:offer_id>', methods=['GET', 'POST'])
@admin_required
def edit_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    form = OfferForm(obj=offer)

    if form.validate_on_submit():
        offer.title = form.title.data
        offer.description = form.description.data
        offer.start_date = form.start_date.data
        offer.end_date = form.end_date.data
        offer.active = form.active.data

        # Handle image upload
        image_data = form.image.data
        if image_data and hasattr(image_data, 'filename') and image_data.filename:
            filename = secure_filename(image_data.filename)
            image_path = os.path.join(current_app.root_path, 'static/uploads', filename)
            try:
                image_data.save(image_path)
                offer.image = filename
            except Exception as e:
                flash(f'Error saving image: {e}', 'danger')
                return redirect(url_for('site.edit_offer', offer_id=offer_id))

        db.session.commit()
        flash('Offer updated successfully!', 'success')
        return redirect(url_for('site.offers'))

    return render_template('edit_offer.html', form=form, offer=offer)


@site_bp.route('/delete_offer/<int:offer_id>', methods=['POST'])
@admin_required
def delete_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    db.session.delete(offer)
    db.session.commit()
    flash('Offer deleted successfully!', 'success')
    return redirect(url_for('site.offers'))

@site_bp.route('/home', methods=['GET', 'POST'])
@admin_required
def client_offers():
    offers = Offer.query.filter_by(active=True).all()
    return render_template('home.html', offers=offers)




@site_bp.route('/about-us', methods=['GET', 'POST'])
@admin_required
def about_us():
    # Fetch the first AboutUs record (or None if it doesn't exist)
    about_us = AboutUs.query.first()
    form = AboutUsForm(obj=about_us)

    if form.validate_on_submit():
        # Create a new AboutUs instance if none exists
        if not about_us:
            about_us = AboutUs()

        # Update AboutUs fields from form data
        about_us.title = form.title.data
        about_us.description = form.description.data

        # Handle image upload
        image_data = form.image.data
        if image_data and hasattr(image_data, 'filename') and image_data.filename:
            filename = secure_filename(image_data.filename)
            image_path = os.path.join(current_app.root_path, 'static/uploads', filename)
            try:
                image_data.save(image_path)
                about_us.image = filename
            except Exception as e:
                flash(f'Error saving image: {e}', 'danger')
                return redirect(url_for('site.about_us'))

        # Add the new AboutUs record to the session if it was newly created
        if not AboutUs.query.first():
            db.session.add(about_us)

        # Commit changes to the database
        try:
            db.session.commit()
            flash('About Us content updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating About Us content: {e}', 'danger')
            return redirect(url_for('site.about_us'))

        return redirect(url_for('site.about_us'))

    return render_template('about_us.html', form=form, about_us=about_us)

@site_bp.route('/manage_blog', methods=['GET', 'POST'])
@admin_required
def manage_blog():
    form = BlogPostForm()
    blog_posts = BlogPost.query.all()
    if form.validate_on_submit():
        post = BlogPost(
            title=form.title.data,
            description=form.description.data
        )
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            image_path = os.path.join(current_app.root_path, 'static/uploads', filename)
            try:
                form.image.data.save(image_path)
                post.image = filename
            except Exception as e:
                flash(f'Error saving image: {e}', 'danger')
                return redirect(url_for('site.manage_blog'))

        db.session.add(post)
        db.session.commit()
        flash('Blog post added successfully!', 'success')
        return redirect(url_for('site.manage_blog'))

    return render_template('manage_blog.html', form=form, blog_posts=blog_posts)

@site_bp.route('/edit-blog/<int:post_id>', methods=['GET', 'POST'])
@admin_required
def edit_blog(post_id):
    post = BlogPost.query.get_or_404(post_id)
    form = BlogPostForm(obj=post)

    if form.validate_on_submit():
        post.title = form.title.data
        post.description = form.description.data

        # Handle image upload
        image_data = form.image.data
        if image_data and hasattr(image_data, 'filename') and image_data.filename:
            filename = secure_filename(image_data.filename)
            image_path = os.path.join(current_app.root_path, 'static/uploads', filename)
            try:
                image_data.save(image_path)
                post.image = filename
            except Exception as e:
                flash(f'Error saving image: {e}', 'danger')
                return redirect(url_for('site.edit_blog', post_id=post_id))

        db.session.commit()
        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('site.manage_blog'))

    return render_template('edit_blog.html', form=form, post=post)


@site_bp.route('/delete-blog/<int:post_id>', methods=['POST'])
@admin_required
def delete_blog(post_id):
    post = BlogPost.query.get_or_404(post_id)
    
    try:
        db.session.delete(post)
        db.session.commit()
        flash('Blog post deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting blog post: {}'.format(str(e)), 'danger')
    
    return redirect(url_for('site.manage_blog'))


@site_bp.route('/promotions', methods=['GET'])
@admin_required
def list_promotions():
    promotions = Promotion.query.all()
    form = PromotionForm()
    return render_template('list_promotions.html', promotions=promotions, form=form)

@site_bp.route('/promotions/add', methods=['GET', 'POST'])
@admin_required
def add_promotion():
    form = PromotionForm()
    if form.validate_on_submit():
        promotion = Promotion(
            name=form.name.data,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data
        )
        db.session.add(promotion)
        db.session.commit()
        return redirect(url_for('site.list_promotions'))
    return render_template('add_promotion.html', form=form)

@site_bp.route('/promotions/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_promotion(id):
    promotion = Promotion.query.get_or_404(id)
    form = PromotionForm(obj=promotion)
    if form.validate_on_submit():
        promotion.name = form.name.data
        promotion.description = form.description.data
        promotion.start_date = form.start_date.data
        promotion.end_date = form.end_date.data
        db.session.commit()
        return redirect(url_for('site.list_promotions'))
    return render_template('edit_promotion.html', form=form, promotion=promotion)

@site_bp.route('/promotions/activate/<int:id>', methods=['POST'])
@admin_required
def activate_promotion(id):
    promotion = Promotion.query.get_or_404(id)
    promotion.active = True
    db.session.commit()
    flash('Promotion activated successfully!', 'success')
    return redirect(url_for('site.list_promotions'))

@site_bp.route('/promotions/deactivate/<int:id>', methods=['POST'])
@admin_required
def deactivate_promotion(id):
    promotion = Promotion.query.get_or_404(id)
    promotion.active = False
    db.session.commit()
    flash('Promotion deactivated successfully!', 'success')
    return redirect(url_for('site.list_promotions'))

@site_bp.route('/promotions/delete/<int:id>', methods=['POST'])
@admin_required
def delete_promotion(id):
    promotion = Promotion.query.get_or_404(id)
    db.session.delete(promotion)
    db.session.commit()
    flash('Promotion deleted successfully!', 'success')
    return redirect(url_for('site.list_promotions'))

@site_bp.route('/promotions/tag_products/<int:id>', methods=['POST'])
@admin_required
def tag_products(id):
    # Get the promotion by ID
    promotion = Promotion.query.get_or_404(id)
    
    # Get the list of product IDs from the form
    product_ids = request.form.getlist('products')
    
    # Retrieve the products by IDs
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    
    # Update each product to include the promotion
    for product in products:
        if promotion not in product.promotions:
            product.promotions.append(promotion)
    
    # Commit the changes to the database
    db.session.commit()
    
    flash('Products tagged successfully!', 'success')
    return redirect(url_for('site.list_promotions'))


@site_bp.route('/promotions/tag_products_modal/<int:id>', methods=['GET'])
@admin_required
def tag_products_modal(id):
    promotion = Promotion.query.get_or_404(id)
    products = Product.query.all()
    
    # Prepare form and populate choices
    form = TagProductsForm()
    form.products.choices = [(product.id, product.brand) for product in products]

    return render_template('tag_products_modal.html', form=form, promotion=promotion)
