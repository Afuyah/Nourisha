"""empty message

Revision ID: fce3df56752b
Revises: 
Create Date: 2024-06-08 16:58:13.422033

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fce3df56752b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('order_item', schema=None) as batch_op:
        batch_op.alter_column('fulfillment_status',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('order_item', schema=None) as batch_op:
        batch_op.alter_column('fulfillment_status',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)

    # ### end Alembic commands ###