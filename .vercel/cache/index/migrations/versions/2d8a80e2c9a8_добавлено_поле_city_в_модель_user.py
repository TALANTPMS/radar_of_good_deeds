"""Добавлено поле city в модель User

Revision ID: 2d8a80e2c9a8
Revises: 0edf13418724
Create Date: 2025-04-08 16:41:45.153559

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d8a80e2c9a8'
down_revision = '0edf13418724'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('city', sa.String(length=100), nullable=True))
        batch_op.drop_column('location')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('location', sa.VARCHAR(length=200), nullable=True))
        batch_op.drop_column('city')

    # ### end Alembic commands ###
