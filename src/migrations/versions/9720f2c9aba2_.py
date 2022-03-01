"""empty message

Revision ID: 9720f2c9aba2
Revises: 25a0a520d83a
Create Date: 2022-02-25 12:53:28.714751

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9720f2c9aba2'
down_revision = '25a0a520d83a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - Renaming column while keeping data ###
    op.create_unique_constraint(None, 'token', ['opaque_token'])
    op.add_column('user', sa.Column('tin', sa.String(), nullable=True))
    op.execute('UPDATE user SET tin = cvr')
    op.drop_index('ix_user_cvr', table_name='user')
    op.create_index(op.f('ix_user_tin'), 'user', ['tin'], unique=False)
    op.create_unique_constraint(None, 'user', ['subject'])
    op.drop_column('user', 'cvr')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - Renaming column while keeping data ###
    op.add_column('user', sa.Column('cvr', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.execute('UPDATE user SET cvr = tin')
    op.drop_constraint(None, 'user', type_='unique')
    op.drop_index(op.f('ix_user_tin'), table_name='user')
    op.create_index('ix_user_cvr', 'user', ['cvr'], unique=False)
    op.drop_column('user', 'tin')
    op.drop_constraint(None, 'token', type_='unique')
    # ### end Alembic commands ###