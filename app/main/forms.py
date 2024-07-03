from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, IntegerField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from flask_wtf.file import FileField, FileRequired, DataRequired
from wtforms import HiddenField, TextAreaField, BooleanField
from wtforms.validators import InputRequired, Optional, Length, NumberRange


class RegistrationForm(FlaskForm):
  name = StringField('Name', validators=[DataRequired()])
  username = StringField('Username', validators=[DataRequired()])
  email = StringField('Email', validators=[DataRequired()])
  phone = StringField('Phone', validators=[DataRequired()])
  password = PasswordField('Password', validators=[DataRequired()])
  submit = SubmitField('Register')

class AddUserForm(FlaskForm):
  username = StringField('Username', validators=[DataRequired()])
  email = StringField('Email', validators=[DataRequired()])
  phone = StringField('Phone', validators=[DataRequired()])
  name = StringField('Full Name')
  submit = SubmitField('Add User')

class LoginForm(FlaskForm):
    # Add the identifier field for username, email, or phone number
    identifier = StringField('Username/Email/Phone', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class AddRoleForm(FlaskForm):
  name = StringField('Role Name', validators=[DataRequired()])
  submit = SubmitField('Add Role')


class EditUserForm(FlaskForm):
  username = StringField('Username',
                         validators=[DataRequired(),
                                     Length(min=4, max=25)])
  email = StringField('Email', validators=[DataRequired(), Email()])
  phone = StringField('Phone',
                      validators=[DataRequired(),
                                  Length(min=10, max=15)])
  name = StringField('Name',
                     validators=[DataRequired(),
                                 Length(min=2, max=50)])
  password = PasswordField('Password', validators=[Length(min=6)])
  submit = SubmitField('Save Changes')


class AddProductCategoryForm(FlaskForm):
  name = StringField('Category Name',
                     validators=[DataRequired(),
                                 Length(max=100)])
  submit = SubmitField('Add Category')


class AddSupplierForm(FlaskForm):
  supplier_id = StringField('Supplier ID', validators=[DataRequired()])
  name = StringField('Name', validators=[DataRequired()])
  contact_person = StringField('Contact Person', validators=[DataRequired()])
  contact_email = StringField('Contact Email', validators=[DataRequired()])
  contact_phone = StringField('Contact Phone', validators=[DataRequired()])
  address = StringField('Address', validators=[DataRequired()])
  city = StringField('City', validators=[DataRequired()])
  submit = SubmitField('Add Supplier')


class AddProductForm(FlaskForm):
  name = StringField('Product Brand', validators=[DataRequired(), Length(max=100)])
  category = SelectField('Category', coerce=int, validators=[DataRequired()])
  brand = StringField('Product name', validators=[Optional(), Length(max=100)])
  unit_price = FloatField('Unit Price', validators=[DataRequired(), NumberRange(min=0)])
  unit_measurement = StringField('Unit of Measurement', validators=[Optional(), Length(max=50)])
  quantity_in_stock = IntegerField('Quantity in Stock', validators=[DataRequired(), NumberRange(min=0)])
  discount_percentage = FloatField('Discount Percentage', validators=[Optional(), NumberRange(min=0, max=100)])
  promotional_tag = StringField('Promotional Tag', validators=[Optional(), Length(max=50)])
  nutritional_information = TextAreaField('Nutritional Information', validators=[Optional()])
  country_of_origin = StringField('Country of Origin', validators=[Optional(), Length(max=50)])
  supplier = SelectField('Supplier', coerce=int, validators=[DataRequired()])
  date_added = DateField('Date Added to Inventory', validators=[DataRequired()])
  submit = SubmitField('Add Product')


class ProductImageForm(FlaskForm):
  product = SelectField('Product', coerce=int, validators=[DataRequired()])
  cover_image = FileField('Cover Image', validators=[FileRequired()])
  image1 = FileField('Image 1', validators=[FileRequired()])
  image2 = FileField('Image 2', validators=[FileRequired()])
  image3 = FileField('Image 3', validators=[FileRequired()])
  submit = SubmitField('Upload Images')


class AddLocationForm(FlaskForm):
  location_name = StringField('Location Name', validators=[DataRequired()])
  submit = SubmitField('Add Location')



class AddArealineForm(FlaskForm):
  name = StringField('Arealine Name', validators=[DataRequired()])
  location = SelectField('Location', coerce=int, validators=[DataRequired()])
  submit = SubmitField('Add Arealine')


class AddNearestPlaceForm(FlaskForm):
  name = StringField('Nearest Place Name', validators=[DataRequired()])
  arealine = SelectField('Arealine', coerce=int, validators=[DataRequired()])
  submit = SubmitField('Add Nearest Place')


class CheckoutForm(FlaskForm):
  full_name = StringField('Full Name', validators=[DataRequired()])
  phone_number = StringField('Phone Number', validators=[DataRequired()])
  alt_phone_number = StringField('Alternative Phone')
  location = SelectField('Select Location', validators=[DataRequired()])
  arealine = SelectField('Select Arealine', validators=[DataRequired()])
  nearest_place = SelectField('Select Nearest Place',
                              validators=[DataRequired()])
  address_line = TextAreaField('Delivery Address', validators=[DataRequired()])
  additional_info = TextAreaField('Special Instructions')
  hidden_custom_description = HiddenField("Custom Description")
  custom_description = TextAreaField('Custom Description')
  payment_method = SelectField('Payment Method',
                               choices=[('pay_on_delivery', 'Pay on Delivery'),
                                        ('pay_now', 'Pay Now')],
                               validators=[DataRequired()])
  submit = SubmitField('Confirm Order')

  # Method to set choices for location
  def set_location_choices(self, locations):
    self.location.choices = [(location.id, location.name)
                             for location in locations]

  # Method to set choices for arealine
  def set_arealine_choices(self, arealines):
    self.arealine.choices = [(arealine.id, arealine.name)
                             for arealine in arealines]

  # Method to set choices for nearest place
  def set_nearest_place_choices(self, nearest_places):
    self.nearest_place.choices = [(place.id, place.name)
                                  for place in nearest_places]



class DateSelectionForm(FlaskForm):
    order_date = DateField('Select Order Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('View Orders')

class FulfillmentForm(FlaskForm):
  hidden_tag = HiddenField()
  expected_delivery_date = DateField('Expected Delivery Date', format='%Y-%m-%d', validators=[DataRequired()])

class ConfirmOrderForm(FlaskForm):
  expected_delivery_date = DateField('Expected Delivery Date', validators=[DataRequired()])
  submit = SubmitField('Confirm Order')

class ExpectedDeliveryDateForm(FlaskForm):
  expected_delivery_date = DateField('Expected Delivery Date', validators=[DataRequired()], format='%Y-%m-%d')
  submit = SubmitField('Confirm Order')

def validate_expected_delivery_date(self, field):
        if field.data < date.today():
            raise ValidationError('Invalid Delivery date')


class ShopForUserForm(FlaskForm):
    user = SelectField('Select User', coerce=int, validators=[DataRequired()])
    product = SelectField('Select Product', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    custom_description = StringField('Custom Description')
