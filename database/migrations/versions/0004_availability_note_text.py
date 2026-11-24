from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column(
        "products",
        "availability_note",
        existing_type=sa.String(255),
        type_=sa.Text(),
    )

def downgrade():
    op.alter_column(
        "products",
        "availability_note",
        existing_type=sa.Text(),
        type_=sa.String(255),
    )
