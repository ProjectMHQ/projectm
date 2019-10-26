"""empty message

Revision ID: 1761237303ed
Revises: 50736469be67
Create Date: 2019-10-26 11:25:42.264624

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1761237303ed'
down_revision = '50736469be67'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('hashed_password',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=64),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('hashed_password',
               existing_type=sa.String(length=64),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)

    # ### end Alembic commands ###
