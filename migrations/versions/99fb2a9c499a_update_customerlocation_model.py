"""Update CustomerLocation model

Revision ID: 99fb2a9c499a
Revises: 
Create Date: 2023-12-23 12:04:12.294116

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '99fb2a9c499a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    inspector = Inspector.from_engine(op.get_bind())

    # Check if the 'order' table exists before making changes
    if inspector.has_table('order'):
        with op.batch_alter_table('order') as batch_op:
            batch_op.drop_constraint(None, type_='foreignkey')
            batch_op.alter_column('product_id',
                existing_type=sa.INTEGER(),
                nullable=False)
            batch_op.create_foreign_key(None, 'customer_order', ['order_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('order') as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('product_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # Recreate the foreign key
    with op.batch_alter_table('order') as batch_op:
        batch_op.create_foreign_key(None, 'order', ['order_id'], ['id'])
    
    # ### end Alembic commands ###
