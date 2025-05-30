"""Add status column to guardian_approvals

Revision ID: 751a148d12e8
Revises: ae6275890d2d
Create Date: 2025-04-14 14:27:53.692533

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '751a148d12e8'
down_revision = 'ae6275890d2d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('guardian_approvals', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('guardian_approvals', schema=None) as batch_op:
        batch_op.drop_column('status')

    # ### end Alembic commands ###
