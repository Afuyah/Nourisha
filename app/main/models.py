from time import time
from datetime import datetime
from flask import request, current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from app import db
from sqlalchemy import event



class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    phone = db.Column(db.String(15), index=True, unique=True)
    name = db.Column(db.String(120))
    password_hash = db.Column(db.String(128))
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_date = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(15))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    confirmed = db.Column(db.Boolean, default=False)
    confirmation_token = db.Column(db.String(64), unique=True)

    # Define the relationship with the Role model
    role = db.relationship('Role', backref=db.backref('users', lazy=True))
    orders = db.relationship('Order', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    
    def set_last_login_info(self):
        self.last_login_date = datetime.utcnow()
        self.last_login_ip = request.remote_addr if request and request.remote_addr else None  

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        self.confirmation_token = s.dumps({'confirm': int(self.id), 'exp': int(time() + expiration)})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        if 'exp' in data and data['exp'] < time():
            # Token has expired
            return False

        if data.get('confirm') != self.id:
            return False

        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True


class ProductCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    # Define the relationship with Product
    products = db.relationship('Product', back_populates='category')

    def __repr__(self):
        return f"<ProductCategory {self.name}>"

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    contact_person = db.Column(db.String(255))
    contact_email = db.Column(db.String(255))
    contact_phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))

    # Define the relationship with Product
    products = db.relationship('Product', back_populates='supplier')



class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('product_category.id'), nullable=False)
    brand = db.Column(db.String(50), nullable=True)
    unit_price = db.Column(db.Float, nullable=False)
    unit_measurement = db.Column(db.String(20), nullable=True)
    quantity_in_stock = db.Column(db.Integer, nullable=False)
    quantity_sold = db.Column(db.Integer, default=0)
    discount_percentage = db.Column(db.Float, nullable=True)
    promotional_tag = db.Column(db.String(50), nullable=True)
    nutritional_information = db.Column(db.Text, nullable=True)
    country_of_origin = db.Column(db.String(50), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    date_added = db.Column(db.Date, nullable=False)
        # Define relationships with Supplier and ProductCategory and images
    supplier = db.relationship('Supplier', back_populates='products')
    category = db.relationship('ProductCategory', back_populates='products')
    images = db.relationship('ProductImage', back_populates='product')
    carts = db.relationship('Cart', back_populates='product')
    #order_items = db.relationship('OrderItem', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', back_populates='product')
  
class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    cover_image = db.Column(db.String(255), nullable=False)
    image1 = db.Column(db.String(255), nullable=True)
    image2 = db.Column(db.String(255), nullable=True)
    image3 = db.Column(db.String(255), nullable=True)
   
    # Define a relationship with Product
    product = db.relationship('Product', back_populates='images')

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
  
    product = db.relationship('Product', back_populates='carts')

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100))
    arealine = db.Column(db.String(255))

    orders = db.relationship('Order', back_populates='location')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # Status can be 'pending', 'confirmed', etc.
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    day_of_week = db.Column(db.Integer)
    expected_delivery_date = db.Column(db.Date)
    total_price = db.Column(db.Float, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    address_line = db.Column(db.Text, nullable=False)
    additional_info = db.Column(db.Text)
    payment_method = db.Column(db.String(50), nullable=False)

    # Payment details
    payment_status = db.Column(db.String(50), default='unpaid')  # 'unpaid', 'paid', etc.
    payment_date = db.Column(db.DateTime)  # Date when payment was made
    transaction_id = db.Column(db.String(100))  # Unique identifier for the payment transaction

    # Phone number used for payment
    phone_number = db.Column(db.String(20), nullable=True)

    # Define the relationship with User
    user = db.relationship('User', back_populates='orders')

    # Define the relationship with Location
    location = db.relationship('Location', back_populates='orders')
    
    # Relationship with OrderItem
    order_items = db.relationship('OrderItem', back_populates='order')
    def update_order_day_of_week(self):
        # Update the day_of_week based on the order_date
        if self.order_date:
            self.day_of_week = self.order_date.strftime('%A')  # Corrected attribute name
            db.session.commit()
    def __init__(self, *args, **kwargs):
        super(Order, self).__init__(*args, **kwargs)
        self.update_order_day_of_week()

@event.listens_for(Order, 'before_insert')
def before_insert_order(mapper, connection, target):
    target.update_order_day_of_week()



class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    # Define the relationship with Order
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    order = db.relationship('Order', back_populates='order_items')
    product = db.relationship('Product', back_populates='order_items')

    def update_product_quantity_sold(self):
        # Update the quantity_sold field for the associated product
        self.product.quantity_sold += self.quantity
        db.session.commit()


