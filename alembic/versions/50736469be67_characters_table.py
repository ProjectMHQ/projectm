"""characters table

Revision ID: 50736469be67
Revises: 57cfabc88321
Create Date: 2019-10-22 20:02:59.881109

"""
from alembic import op
import sqlalchemy as sa
import core

# revision identifiers, used by Alembic.
revision = '50736469be67'
down_revision = '57cfabc88321'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('character',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('character_id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=32), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
    sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
    sa.Column('meta', core.src.auth.database.json_column_type(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('character', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_character_character_id'), ['character_id'], unique=True)
        batch_op.create_index(batch_op.f('ix_character_name'), ['name'], unique=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('character', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_character_name'))
        batch_op.drop_index(batch_op.f('ix_character_character_id'))

    op.drop_table('character')
    # ### end Alembic commands ###
