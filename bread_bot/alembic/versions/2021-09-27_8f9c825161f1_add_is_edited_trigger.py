"""Add is edited trigger

Revision ID: 8f9c825161f1
Revises: 89a2d8aa7a11
Create Date: 2021-09-27 22:53:13.581933

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f9c825161f1'
down_revision = '89a2d8aa7a11'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chats',
                  sa.Column('is_edited_trigger', sa.Boolean(), nullable=True))
    op.execute("UPDATE chats SET is_edited_trigger = false")
    op.alter_column('chats', 'is_edited_trigger', nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('chats', 'is_edited_trigger')
    # ### end Alembic commands ###