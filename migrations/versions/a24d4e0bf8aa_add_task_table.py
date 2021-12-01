"""add task table

Revision ID: a24d4e0bf8aa
Revises: f5f55452fa58
Create Date: 2021-11-24 23:57:23.982602

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a24d4e0bf8aa'
down_revision = 'f5f55452fa58'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('task',
    sa.Column('task_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('checkpoint_id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('kpi_id', sa.Integer(), nullable=False),
    sa.Column('analytics_type', sa.String(length=80), nullable=False),
    sa.Column('checkpoint', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=80), nullable=False),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('task_id', 'checkpoint_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('task')
    # ### end Alembic commands ###
