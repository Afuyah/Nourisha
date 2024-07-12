"""added fulfillment status and modified purchase table

Revision ID: bed7fcab0326
Revises: 
Create Date: 2024-07-12 11:59:01.511098

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bed7fcab0326'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Check if fulfillment_status column exists before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns('order_item')
    column_names = [column['name'] for column in columns]

    if 'fulfillment_status' not in column_names:
        with op.batch_alter_table('order_item', schema=None) as batch_op:
            batch_op.add_column(sa.Column('fulfillment_status', sa.String(length=20), nullable=True))

    with op.batch_alter_table('purchase', schema=None) as batch_op:
        batch_op.add_column(sa.Column('order_item_id', sa.Integer(), nullable=False))

        # Get the name of the existing foreign key constraint
        foreign_keys = inspector.get_foreign_keys('purchase')
        fk_name = foreign_keys[0]['name'] if foreign_keys else None

        if fk_name:
            batch_op.drop_constraint(fk_name, type_='foreignkey')

        batch_op.create_foreign_key(
            'fk_purchase_order_item_id_order_item', 'order_item', ['order_item_id'], ['id']
        )

        batch_op.drop_column('order_id')

    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('purchase', schema=None) as batch_op:
        batch_op.add_column(sa.Column('order_id', sa.INTEGER(), nullable=False))

        # Get the name of the existing foreign key constraint
        foreign_keys = inspector.get_foreign_keys('purchase')
        fk_name = foreign_keys[0]['name'] if foreign_keys else None

        if fk_name:
            batch_op.drop_constraint(fk_name, type_='foreignkey')

        batch_op.create_foreign_key('fk_purchase_order_id_order_item', 'order_item', ['order_id'], ['id'])
        
        batch_op.drop_column('order_item_id')

    with op.batch_alter_table('order_item', schema=None) as batch_op:
        batch_op.drop_column('fulfillment_status')

    # ### end Alembic commands ###
