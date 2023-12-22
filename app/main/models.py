from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request
from app import db

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

    # Define the relationship with the Role model
    role = db.relationship('Role', backref=db.backref('users', lazy=True))
    orders = db.relationship('Order', backref='customer', lazy='dynamic')
  
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_last_login_info(self):
        self.last_login_date = datetime.utcnow()
        self.last_login_ip = request.remote_addr


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
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_address = db.Column(db.String(255), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    order_status = db.Column(db.String(50), nullable=False)
    payment_status = db.Column(db.String(50), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    delivery_date_time = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    # Define relationships if needed
    items = db.relationship('OrderItem', back_populates='order')
    user = db.relationship('User', back_populates='orders')
    

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    # Define relationships
    order = db.relationship('Order', back_populates='items')
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    product = db.relationship('Product', backref='order_item_product', uselist=False)