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

# Role model for user roles
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
  password_hash = db.Column(db.String(5000))
  registration_date = db.Column(db.DateTime, default=datetime.utcnow)
  last_login_date = db.Column(db.DateTime)
  last_login_ip = db.Column(db.String(15))
  role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
  confirmed = db.Column(db.Boolean, default=False)
  confirmation_token = db.Column(db.String(64), unique=True)

  preferred_categories = db.Column(db.Text)  # JSON or CSV of preferred category IDs
  average_spending = db.Column(db.Float)  # Average spending per order
  purchase_frequency = db.Column(db.Integer)  # Number of orders per month
  last_active = db.Column(db.DateTime)  # Last activity timestamp

  delivery_info = db.relationship('UserDeliveryInfo',
                                  back_populates='user',
                                  lazy='dynamic')

  role = db.relationship('Role', backref=db.backref('users', lazy=True))
  orders = db.relationship('Order', back_populates='user')
  clicks = db.relationship('ProductClick', back_populates='user')
  views = db.relationship('ProductView', back_populates='user')
  search_queries = db.relationship('UserSearchQuery', back_populates='user')
  ratings = db.relationship('Rating', back_populates='user')  # New relationship for ratings

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
          # Token has expired
          return False

      if data.get('confirm') != self.id:
          return False

      self.confirmed = True
      db.session.add(self)
      db.session.commit()
      return True

    # Method to calculate and update average spending per order
  def update_average_spending(self):
      orders = Order.query.filter_by(user_id=self.id).all()
      if orders:
          total_spent = sum(order.total_price for order in orders)
          self.average_spending = total_spent / len(orders)
      else:
          self.average_spending = 0.0

    # Method to update purchase frequency
  def update_purchase_frequency(self):
      orders = Order.query.filter_by(user_id=self.id).all()
      if orders:
          self.purchase_frequency = len(orders)
      else:
          self.purchase_frequency = 0
   # Method to update last active timestamp
  def update_last_active(self):
      self.last_active = datetime.utcnow()
   # Method to fetch user ratings for collaborative filtering
  def fetch_ratings(self):
      return Rating.query.filter_by(user_id=self.id).all()
# Rating model to capture user ratings for products
class Rating(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
  rating = db.Column(db.Float, nullable=False)
  user = db.relationship('User', back_populates='ratings')
  product = db.relationship('Product', back_populates='ratings')

  def __repr__(self):
      return f'<Rating {self.rating}>'

# ProductCategory model for product categories
class ProductCategory(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False, unique=True)

  # Define the relationship with Product
  products = db.relationship('Product', back_populates='category')

  def __repr__(self):
    return f"<ProductCategory {self.name}>"


# Supplier model for handling information about product suppliers
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
  average_rating = db.Column(db.Float)  # Average user rating
  click_count = db.Column(db.Integer, default=0)  # Number of times the product was clicked
  view_count = db.Column(db.Integer, default=0)  # Number of times the product was viewed
  supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
  date_added = db.Column(db.Date, nullable=False)

    # Define relationships with Supplier, ProductCategory, and images
  supplier = db.relationship('Supplier', back_populates='products')
  category = db.relationship('ProductCategory', back_populates='products')
  images = db.relationship('ProductImage', back_populates='product')
  carts = db.relationship('Cart', back_populates='product')
  order_items = db.relationship('OrderItem', back_populates='product')

    # Add relationships to the interaction models
  clicks = db.relationship('ProductClick', back_populates='product')
  views = db.relationship('ProductView', back_populates='product')
  ratings = db.relationship('Rating', back_populates='product')
class ProductClick(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
  timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
  user = db.relationship('User', back_populates='clicks')
  product = db.relationship('Product', back_populates='clicks')

class ProductView(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
  timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
  user = db.relationship('User', back_populates='views')
  product = db.relationship('Product', back_populates='views')

class UserSearchQuery(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  query_text = db.Column(db.String(255), nullable=False)
  timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with the user
  user = db.relationship('User', back_populates='search_queries')





# ProductImage model for handling product images
class ProductImage(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  product_id = db.Column(db.Integer,
                         db.ForeignKey('product.id'),
                         nullable=False)
  cover_image = db.Column(db.String(255), nullable=False)
  image1 = db.Column(db.String(255), nullable=True)
  image2 = db.Column(db.String(255), nullable=True)
  image3 = db.Column(db.String(255), nullable=True)

  # Define a relationship with Product
  product = db.relationship('Product', back_populates='images')


class Cart(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  product_id = db.Column(db.Integer,
                         db.ForeignKey('product.id'),
                         nullable=False)
  quantity = db.Column(db.Integer, nullable=False)
  product = db.relationship('Product', back_populates='carts')
  custom_description = db.Column(db.Text)


# Order model for handling user orders
class Order(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  status = db.Column(db.String(50), default='pending')
  order_date = db.Column(db.DateTime, default=datetime.utcnow)
  expected_delivery_date = db.Column(db.Date)
  total_price = db.Column(db.Float, nullable=False)
  custom_description = db.Column(db.Text)
  location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
  arealine_id = db.Column(db.Integer, db.ForeignKey('arealine.id'), nullable=False)
  nearest_place_id = db.Column(db.Integer, db.ForeignKey('nearest_place.id'), nullable=False)
  address_line = db.Column(db.String(500), nullable=False)
  additional_info = db.Column(db.Text)
  payment_method = db.Column(db.String(50), nullable=False)
  payment_status = db.Column(db.String(50), default='unpaid')
  payment_date = db.Column(db.DateTime)
  transaction_id = db.Column(db.String(100))
  phone_number = db.Column(db.String(20))
  delivery_remarks = db.Column(db.Text)

  user = db.relationship('User', back_populates='orders')
  location = db.relationship('Location', back_populates='orders')
  arealine = db.relationship('Arealine', back_populates='orders')
  nearest_place = db.relationship('NearestPlace', back_populates='orders')
  order_items = db.relationship('OrderItem', back_populates='order')

  def calculate_fulfilled_total(self):
        fulfilled_items_total = sum(item.total_price for item in self.order_items if item.fulfillment_status == 'fulfilled')
        return fulfilled_items_total + 200  # Adding the shipping fee



class OrderItem(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
  product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
  quantity = db.Column(db.Integer, nullable=False)
  unit_price = db.Column(db.Float, nullable=False)
  custom_description = db.Column(db.Text)
  fulfillment_status = db.Column(db.String(20), nullable=False, default='Not fulfilled')

  order = db.relationship('Order', back_populates='order_items')
  product = db.relationship('Product', back_populates='order_items')

  @hybrid_property
  def total_price(self):
        return self.quantity * self.unit_price

  

class Location(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False, unique=True)
  arealines = db.relationship('Arealine', back_populates='location')
  orders = db.relationship('Order', back_populates='location')
  user_delivery_info = db.relationship('UserDeliveryInfo', back_populates='location')
  
class Arealine(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255), nullable=False)
  location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
  location = db.relationship('Location', back_populates='arealines')
  nearest_places = db.relationship('NearestPlace', back_populates='arealine')
  user_delivery_info = db.relationship('UserDeliveryInfo', back_populates='arealine')
  orders = db.relationship('Order', back_populates='arealine')


class NearestPlace(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255), nullable=False)
  arealine_id = db.Column(db.Integer, db.ForeignKey('arealine.id'), nullable=False)  
  arealine = db.relationship('Arealine', back_populates='nearest_places')
  orders = db.relationship('Order', back_populates='nearest_place')
  user_delivery_info = db.relationship('UserDeliveryInfo', back_populates='nearest_place')


class UserDeliveryInfo(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
  arealine_id = db.Column(db.Integer, db.ForeignKey('arealine.id'), nullable=False)
  nearest_place_id = db.Column(db.Integer, db.ForeignKey('nearest_place.id'), nullable=False)
  address_line = db.Column(db.String(500))
  full_name = db.Column(db.String(100))
  phone_number = db.Column(db.String(20))
  alt_phone_number = db.Column(db.String(20))
  additional_info = db.Column(db.Text)
  timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)

  user = db.relationship('User', back_populates='delivery_info')
  location = db.relationship('Location', back_populates='user_delivery_info')
  arealine = db.relationship('Arealine', back_populates='user_delivery_info')
  nearest_place = db.relationship('NearestPlace', back_populates='user_delivery_info')
