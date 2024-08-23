from time import time
from datetime import datetime
from flask import request, current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from app import db
from sqlalchemy import event
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Numeric

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)

    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'




class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, index=True, nullable=True)
    name = db.Column(db.String(120))
    password_hash = db.Column(db.String(5000))
    registration_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_login_date = db.Column(db.DateTime, index=True)
    last_login_ip = db.Column(db.String(15))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), index=True)
    confirmed = db.Column(db.Boolean, default=False)
    confirmation_token = db.Column(db.String(64), unique=True)

    preferred_categories = db.Column(db.Text)  # JSON or CSV of preferred category IDs
    average_spending = db.Column(db.Float, default=0.0)
    purchase_frequency = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)

    purchases = db.relationship('Purchase', back_populates='user', lazy='dynamic')
    orders = db.relationship('Order', back_populates='user', lazy='dynamic')
    clicks = db.relationship('ProductClick', back_populates='user', lazy='dynamic')
    views = db.relationship('ProductView', back_populates='user', lazy='dynamic')
    search_queries = db.relationship('UserSearchQuery', back_populates='user', lazy='dynamic')
    ratings = db.relationship('Rating', back_populates='user', lazy='dynamic')
    bought_items = db.relationship('OrderItem', back_populates='bought_by_admin', foreign_keys='OrderItem.bought_by_admin_id', lazy='dynamic')
    delivery_infos = db.relationship('UserDeliveryInfo', back_populates='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_last_login_info(self):
        self.last_login_date = datetime.utcnow()
        self.last_login_ip = request.remote_addr if request and request.remote_addr else None

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        self.confirmation_token = s.dumps({
            'confirm': int(self.id),
            'exp': int(time() + expiration)
        })

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        if 'exp' in data and data['exp'] < time():
            return False

        if data.get('confirm') != self.id:
            return False

        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    def update_average_spending(self):
        total_spent = db.session.query(db.func.sum(Order.total_price)).filter_by(user_id=self.id).scalar() or 0
        order_count = db.session.query(db.func.count(Order.id)).filter_by(user_id=self.id).scalar() or 1
        self.average_spending = total_spent / order_count

    def update_purchase_frequency(self):
        self.purchase_frequency = db.session.query(db.func.count(Order.id)).filter_by(user_id=self.id).scalar() or 0

    def update_last_active(self):
        self.last_active = datetime.utcnow()

    def fetch_ratings(self):
        return Rating.query.filter_by(user_id=self.id).all()

    def has_role(self, role_name):
        return self.role.name == role_name



class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    old_price = db.Column(db.Float, nullable=False)
    new_price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    product = db.relationship('Product', backref='price_histories', lazy='joined')



class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    rating = db.Column(db.Float, nullable=False)

    user = db.relationship('User', back_populates='ratings', lazy='joined')
    product = db.relationship('Product', back_populates='ratings', lazy='joined')

    def __repr__(self):
        return f'<Rating {self.rating}>'


class ProductCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(100), nullable=True)
    tagline = db.Column(db.String(150), nullable=True)

    products = db.relationship('Product', back_populates='category', lazy='dynamic')

    def __repr__(self):
        return f"<ProductCategory {self.name}>"




class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    contact_person = db.Column(db.String(255))
    contact_email = db.Column(db.String(255))
    contact_phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))

    products = db.relationship('Product', back_populates='supplier', lazy='dynamic')




class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('product_category.id'), nullable=False, index=True)
    brand = db.Column(db.String(50), nullable=True)
    unit_price = db.Column(db.Float, nullable=False)
    unit_measurement_id = db.Column(db.Integer, db.ForeignKey('unit_of_measurement.id'), nullable=True)

    quantity_in_stock = db.Column(db.Integer, nullable=False)
    quantity_sold = db.Column(db.Integer, default=0)
    discount_percentage = db.Column(db.Float, nullable=True)
    nutritional_information = db.Column(db.Text, nullable=True)
    country_of_origin = db.Column(db.String(50), nullable=True)
    average_rating = db.Column(db.Float, default=0.0)
    click_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False, index=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    supplier = db.relationship('Supplier', back_populates='products', lazy='joined')
    category = db.relationship('ProductCategory', back_populates='products', lazy='joined')
    images = db.relationship('ProductImage', back_populates='product', lazy='dynamic')
    carts = db.relationship('Cart', back_populates='product', lazy='dynamic')
    order_items = db.relationship('OrderItem', back_populates='product', lazy='dynamic')

    clicks = db.relationship('ProductClick', back_populates='product', lazy='dynamic')
    views = db.relationship('ProductView', back_populates='product', lazy='dynamic')
    ratings = db.relationship('Rating', back_populates='product', lazy='dynamic')
    promotions = db.relationship('Promotion', secondary='product_promotions', backref=db.backref('products', lazy='dynamic'))

    unit_of_measurement = db.relationship('UnitOfMeasurement', back_populates='products', lazy='joined')



class ProductClick(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    guest_ip = db.Column(db.String(45), nullable=True, index=True) 
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', back_populates='clicks', lazy='joined')
    product = db.relationship('Product', back_populates='clicks', lazy='joined')

class ProductView(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    guest_ip = db.Column(db.String(45), nullable=True, index=True) 
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', back_populates='views', lazy='joined')
    product = db.relationship('Product', back_populates='views', lazy='joined')


class UnitOfMeasurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit = db.Column(db.String(50), unique=True, nullable=False, index=True)
    added_by = db.Column(db.String(100), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    products = db.relationship('Product', back_populates='unit_of_measurement', lazy='dynamic')






class UserSearchQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    query_text = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', back_populates='search_queries', lazy='joined')






class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    cover_image = db.Column(db.String(255), nullable=False)
    image1 = db.Column(db.String(255), nullable=True)
    image2 = db.Column(db.String(255), nullable=True)
    image3 = db.Column(db.String(255), nullable=True)

    product = db.relationship('Product', back_populates='images', lazy='joined')



class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    custom_description = db.Column(db.Text)

    # Relationships
    product = db.relationship('Product', back_populates='carts', lazy='joined')

    __table_args__ = (
        db.Index('idx_cart_user_product', 'user_id', 'product_id'),
    )


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    status = db.Column(db.String(50), default='pending', index=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expected_delivery_date = db.Column(db.Date)
    total_price = db.Column(db.Float, nullable=False)
    custom_description = db.Column(db.Text)
    additional_info = db.Column(db.Text)
    delivery_info_id = db.Column(db.Integer, db.ForeignKey('user_delivery_info.id'), nullable=True, index=True)
    payment_method = db.Column(db.String(50), nullable=False, index=True)
    payment_status = db.Column(db.String(50), default='unpaid', index=True)
    delivery_remarks = db.Column(db.Text)
    phone_number = db.Column(db.String(20))

    # Relationships
    user = db.relationship('User', back_populates='orders', lazy='joined')
    delivery_info = db.relationship('UserDeliveryInfo', back_populates='orders', lazy='joined')
    order_items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan', lazy='dynamic')
    payments = db.relationship('Payment', back_populates='order', cascade='all, delete-orphan', lazy='dynamic')

    __table_args__ = (
        db.Index('idx_order_user_status_date', 'user_id', 'status', 'order_date'),
    )

    def calculate_fulfilled_total(self):
        fulfilled_items_total = sum(item.total_price for item in self.order_items if item.fulfillment_status == 'fulfilled')
        return fulfilled_items_total + 200  # Adding the shipping fee



class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, index=True)
    transaction_id = db.Column(db.String(100), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    order = db.relationship('Order', back_populates='payments', lazy='joined')

    __table_args__ = (
        db.Index('idx_payment_order_date', 'order_id', 'payment_date'),
    )





class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    custom_description = db.Column(db.String(255), nullable=True)
    unit_price = db.Column(db.Float, nullable=False)
    purchase_price = db.Column(db.Float, nullable=True)
    bought_by_admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    purchase_status = db.Column(db.String(50), nullable=True, default='Not bought')
    fulfillment_status = db.Column(db.String(20), nullable=True, default='Not fulfilled')

    # Relationships
    order = db.relationship('Order', back_populates='order_items', lazy='joined')
    product = db.relationship('Product', back_populates='order_items', lazy='joined')
    bought_by_admin = db.relationship('User', back_populates='bought_items', foreign_keys=[bought_by_admin_id], lazy='joined')
    purchases = db.relationship('Purchase', back_populates='order_item', lazy='dynamic')

    __table_args__ = (
        db.Index('idx_order_item_order_product', 'order_id', 'product_id'),
    )

    @hybrid_property
    def total_price(self):
        return self.quantity * self.unit_price



class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_item.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    unit_price_bought = db.Column(db.Float, nullable=False)
    quantity_bought = db.Column(db.Integer, nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)

    # Relationships
    order_item = db.relationship('OrderItem', back_populates='purchases', lazy='joined')
    user = db.relationship('User', back_populates='purchases', lazy='joined')

    __table_args__ = (
        db.Index('idx_purchase_order_item_user', 'order_item_id', 'user_id'),
    )



class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    arealines = db.relationship('Arealine', back_populates='location', lazy='dynamic')
    user_delivery_infos = db.relationship('UserDeliveryInfo', back_populates='location', lazy='dynamic')



class Arealine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False, index=True)
    location = db.relationship('Location', back_populates='arealines', lazy='joined')
    user_delivery_infos = db.relationship('UserDeliveryInfo', back_populates='arealine', lazy='dynamic')




class UserDeliveryInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    alt_phone_number = db.Column(db.String(20))
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False, index=True)
    arealine_id = db.Column(db.Integer, db.ForeignKey('arealine.id'), nullable=False, index=True)
    nearest_place = db.Column(db.String(255))
    address_line = db.Column(db.String(500), nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='delivery_infos', lazy='joined')
    location = db.relationship('Location', back_populates='user_delivery_infos', lazy='joined')
    arealine = db.relationship('Arealine', back_populates='user_delivery_infos', lazy='joined')
    orders = db.relationship('Order', back_populates='delivery_info', lazy='dynamic')

 
    
   
class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    image = db.Column(db.String(100), nullable=True)
    start_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    end_date = db.Column(db.DateTime, nullable=False, index=True)
    active = db.Column(db.Boolean, default=True)

    __table_args__ = (
        db.Index('idx_offer_dates_active', 'start_date', 'end_date', 'active'),
    )

    def __repr__(self):
        return f'<Offer {self.title}>'



class AboutUs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<AboutUs {self.title}>'


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255), nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<BlogPost {self.title}>'



class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<ContactMessage {self.id}>'
 

class Promotion(db.Model):
    __tablename__ = 'promotions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=False, index=True)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)

    def __repr__(self):
        return f'<Promotion {self.name}>'



class ProductPromotion(db.Model):
    __tablename__ = 'product_promotions'

    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True, index=True)
    promotion_id = db.Column(db.Integer, db.ForeignKey('promotions.id'), primary_key=True, index=True)

    __table_args__ = (
        db.Index('idx_product_promotion', 'product_id', 'promotion_id'),
    )

  
  