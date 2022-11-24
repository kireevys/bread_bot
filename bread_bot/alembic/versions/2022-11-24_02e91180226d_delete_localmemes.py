"""Delete localmemes

Revision ID: 02e91180226d
Revises: a0dcf3970818
Create Date: 2022-11-24 03:11:32.849497

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '02e91180226d'
down_revision = 'a0dcf3970818'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('local_memes')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('local_memes',
    sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('chat_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('type', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('data', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('data_voice', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('data_photo', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('data_sticker', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['chat_id'], ['chats.chat_id'], name='local_memes_chat_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='local_memes_pkey')
    )
    # ### end Alembic commands ###
