"""empty message

Revision ID: daae93578397
Revises: 98cd24592fc7
Create Date: 2024-06-16 05:10:29.458738

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'daae93578397'
down_revision = '98cd24592fc7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('average_rating', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('click_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('view_count', sa.Integer(), nullable=True))

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('preferred_categories', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('average_spending', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('purchase_frequency', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('last_active', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('last_active')
        batch_op.drop_column('purchase_frequency')
        batch_op.drop_column('average_spending')
        batch_op.drop_column('preferred_categories')

    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.drop_column('view_count')
        batch_op.drop_column('click_count')
        batch_op.drop_column('average_rating')

    # ### end Alembic commands ###