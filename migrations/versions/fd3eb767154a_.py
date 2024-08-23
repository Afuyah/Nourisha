"""empty message

Revision ID: fd3eb767154a
Revises: 
Create Date: 2024-08-23 08:47:48.150856

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd3eb767154a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('about_us', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_about_us_title'), ['title'], unique=False)
        batch_op.create_index(batch_op.f('ix_about_us_updated_at'), ['updated_at'], unique=False)

    with op.batch_alter_table('arealine', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_arealine_location_id'), ['location_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_arealine_name'), ['name'], unique=False)

    with op.batch_alter_table('blog_post', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_blog_post_date_posted'), ['date_posted'], unique=False)
        batch_op.create_index(batch_op.f('ix_blog_post_title'), ['title'], unique=False)

    with op.batch_alter_table('cart', schema=None) as batch_op:
        batch_op.create_index('idx_cart_user_product', ['user_id', 'product_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_cart_product_id'), ['product_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_cart_user_id'), ['user_id'], unique=False)

    with op.batch_alter_table('contact_message', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_contact_message_email'), ['email'], unique=False)
        batch_op.create_index(batch_op.f('ix_contact_message_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_contact_message_timestamp'), ['timestamp'], unique=False)

    with op.batch_alter_table('location', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_location_name'), ['name'], unique=True)

    with op.batch_alter_table('offer', schema=None) as batch_op:
        batch_op.create_index('idx_offer_dates_active', ['start_date', 'end_date', 'active'], unique=False)
        batch_op.create_index(batch_op.f('ix_offer_end_date'), ['end_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_offer_start_date'), ['start_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_offer_title'), ['title'], unique=False)

    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.create_index('idx_order_user_status_date', ['user_id', 'status', 'order_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_order_delivery_info_id'), ['delivery_info_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_order_order_date'), ['order_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_order_payment_method'), ['payment_method'], unique=False)
        batch_op.create_index(batch_op.f('ix_order_payment_status'), ['payment_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_order_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_order_user_id'), ['user_id'], unique=False)

    with op.batch_alter_table('order_item', schema=None) as batch_op:
        batch_op.create_index('idx_order_item_order_product', ['order_id', 'product_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_order_item_bought_by_admin_id'), ['bought_by_admin_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_order_item_order_id'), ['order_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_order_item_product_id'), ['product_id'], unique=False)

    with op.batch_alter_table('payment', schema=None) as batch_op:
        batch_op.create_index('idx_payment_order_date', ['order_id', 'payment_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_payment_order_id'), ['order_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_payment_payment_date'), ['payment_date'], unique=False)

    with op.batch_alter_table('price_history', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_price_history_product_id'), ['product_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_price_history_timestamp'), ['timestamp'], unique=False)

    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_product_category_id'), ['category_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_product_date_added'), ['date_added'], unique=False)
        batch_op.create_index(batch_op.f('ix_product_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_product_supplier_id'), ['supplier_id'], unique=False)

    with op.batch_alter_table('product_category', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_product_category_name'), ['name'], unique=True)

    with op.batch_alter_table('product_click', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_product_click_product_id'), ['product_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_product_click_timestamp'), ['timestamp'], unique=False)
        batch_op.create_index(batch_op.f('ix_product_click_user_id'), ['user_id'], unique=False)

    with op.batch_alter_table('product_image', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_product_image_product_id'), ['product_id'], unique=False)

    with op.batch_alter_table('product_promotions', schema=None) as batch_op:
        batch_op.create_index('idx_product_promotion', ['product_id', 'promotion_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_product_promotions_product_id'), ['product_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_product_promotions_promotion_id'), ['promotion_id'], unique=False)

    with op.batch_alter_table('product_view', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_product_view_product_id'), ['product_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_product_view_timestamp'), ['timestamp'], unique=False)
        batch_op.create_index(batch_op.f('ix_product_view_user_id'), ['user_id'], unique=False)

    with op.batch_alter_table('promotions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_promotions_active'), ['active'], unique=False)
        batch_op.create_index(batch_op.f('ix_promotions_end_date'), ['end_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_promotions_name'), ['name'], unique=True)
        batch_op.create_index(batch_op.f('ix_promotions_start_date'), ['start_date'], unique=False)

    with op.batch_alter_table('purchase', schema=None) as batch_op:
        batch_op.create_index('idx_purchase_order_item_user', ['order_item_id', 'user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_purchase_order_item_id'), ['order_item_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_purchase_purchase_date'), ['purchase_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_purchase_user_id'), ['user_id'], unique=False)

    with op.batch_alter_table('rating', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_rating_product_id'), ['product_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_rating_user_id'), ['user_id'], unique=False)

    with op.batch_alter_table('role', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_role_name'), ['name'], unique=True)

    with op.batch_alter_table('supplier', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_supplier_supplier_id'), ['supplier_id'], unique=True)

    with op.batch_alter_table('unit_of_measurement', schema=None) as batch_op:
        batch_op.alter_column('date_added',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.create_index(batch_op.f('ix_unit_of_measurement_date_added'), ['date_added'], unique=False)
        batch_op.create_index(batch_op.f('ix_unit_of_measurement_unit'), ['unit'], unique=True)

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('username',
               existing_type=sa.VARCHAR(length=64),
               nullable=False)
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=120),
               nullable=False)
        batch_op.create_index(batch_op.f('ix_user_last_login_date'), ['last_login_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_registration_date'), ['registration_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_role_id'), ['role_id'], unique=False)

    with op.batch_alter_table('user_delivery_info', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_delivery_info_arealine_id'), ['arealine_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_delivery_info_location_id'), ['location_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_delivery_info_user_id'), ['user_id'], unique=False)

    with op.batch_alter_table('user_search_query', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_search_query_timestamp'), ['timestamp'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_search_query_user_id'), ['user_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_search_query', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_search_query_user_id'))
        batch_op.drop_index(batch_op.f('ix_user_search_query_timestamp'))

    with op.batch_alter_table('user_delivery_info', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_delivery_info_user_id'))
        batch_op.drop_index(batch_op.f('ix_user_delivery_info_location_id'))
        batch_op.drop_index(batch_op.f('ix_user_delivery_info_arealine_id'))

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_role_id'))
        batch_op.drop_index(batch_op.f('ix_user_registration_date'))
        batch_op.drop_index(batch_op.f('ix_user_last_login_date'))
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=120),
               nullable=True)
        batch_op.alter_column('username',
               existing_type=sa.VARCHAR(length=64),
               nullable=True)

    with op.batch_alter_table('unit_of_measurement', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_unit_of_measurement_unit'))
        batch_op.drop_index(batch_op.f('ix_unit_of_measurement_date_added'))
        batch_op.alter_column('date_added',
               existing_type=sa.DATETIME(),
               nullable=False)

    with op.batch_alter_table('supplier', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_supplier_supplier_id'))

    with op.batch_alter_table('role', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_role_name'))

    with op.batch_alter_table('rating', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_rating_user_id'))
        batch_op.drop_index(batch_op.f('ix_rating_product_id'))

    with op.batch_alter_table('purchase', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_purchase_user_id'))
        batch_op.drop_index(batch_op.f('ix_purchase_purchase_date'))
        batch_op.drop_index(batch_op.f('ix_purchase_order_item_id'))
        batch_op.drop_index('idx_purchase_order_item_user')

    with op.batch_alter_table('promotions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_promotions_start_date'))
        batch_op.drop_index(batch_op.f('ix_promotions_name'))
        batch_op.drop_index(batch_op.f('ix_promotions_end_date'))
        batch_op.drop_index(batch_op.f('ix_promotions_active'))

    with op.batch_alter_table('product_view', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_product_view_user_id'))
        batch_op.drop_index(batch_op.f('ix_product_view_timestamp'))
        batch_op.drop_index(batch_op.f('ix_product_view_product_id'))

    with op.batch_alter_table('product_promotions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_product_promotions_promotion_id'))
        batch_op.drop_index(batch_op.f('ix_product_promotions_product_id'))
        batch_op.drop_index('idx_product_promotion')

    with op.batch_alter_table('product_image', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_product_image_product_id'))

    with op.batch_alter_table('product_click', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_product_click_user_id'))
        batch_op.drop_index(batch_op.f('ix_product_click_timestamp'))
        batch_op.drop_index(batch_op.f('ix_product_click_product_id'))

    with op.batch_alter_table('product_category', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_product_category_name'))

    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_product_supplier_id'))
        batch_op.drop_index(batch_op.f('ix_product_name'))
        batch_op.drop_index(batch_op.f('ix_product_date_added'))
        batch_op.drop_index(batch_op.f('ix_product_category_id'))

    with op.batch_alter_table('price_history', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_price_history_timestamp'))
        batch_op.drop_index(batch_op.f('ix_price_history_product_id'))

    with op.batch_alter_table('payment', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_payment_payment_date'))
        batch_op.drop_index(batch_op.f('ix_payment_order_id'))
        batch_op.drop_index('idx_payment_order_date')

    with op.batch_alter_table('order_item', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_order_item_product_id'))
        batch_op.drop_index(batch_op.f('ix_order_item_order_id'))
        batch_op.drop_index(batch_op.f('ix_order_item_bought_by_admin_id'))
        batch_op.drop_index('idx_order_item_order_product')

    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_order_user_id'))
        batch_op.drop_index(batch_op.f('ix_order_status'))
        batch_op.drop_index(batch_op.f('ix_order_payment_status'))
        batch_op.drop_index(batch_op.f('ix_order_payment_method'))
        batch_op.drop_index(batch_op.f('ix_order_order_date'))
        batch_op.drop_index(batch_op.f('ix_order_delivery_info_id'))
        batch_op.drop_index('idx_order_user_status_date')

    with op.batch_alter_table('offer', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_offer_title'))
        batch_op.drop_index(batch_op.f('ix_offer_start_date'))
        batch_op.drop_index(batch_op.f('ix_offer_end_date'))
        batch_op.drop_index('idx_offer_dates_active')

    with op.batch_alter_table('location', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_location_name'))

    with op.batch_alter_table('contact_message', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_contact_message_timestamp'))
        batch_op.drop_index(batch_op.f('ix_contact_message_name'))
        batch_op.drop_index(batch_op.f('ix_contact_message_email'))

    with op.batch_alter_table('cart', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_cart_user_id'))
        batch_op.drop_index(batch_op.f('ix_cart_product_id'))
        batch_op.drop_index('idx_cart_user_product')

    with op.batch_alter_table('blog_post', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_blog_post_title'))
        batch_op.drop_index(batch_op.f('ix_blog_post_date_posted'))

    with op.batch_alter_table('arealine', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_arealine_name'))
        batch_op.drop_index(batch_op.f('ix_arealine_location_id'))

    with op.batch_alter_table('about_us', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_about_us_updated_at'))
        batch_op.drop_index(batch_op.f('ix_about_us_title'))

    # ### end Alembic commands ###
