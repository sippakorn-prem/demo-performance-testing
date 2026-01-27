"""Add foreign key to cart_items

Revision ID: 002_add_fk
Revises: 001_initial
Create Date: 2026-01-27 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_fk'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add foreign key constraint if it doesn't exist
    # Migration 001 may have already created it (if using updated version)
    # Use PostgreSQL DO block to conditionally create the constraint
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_cart_items_product_id' 
                AND table_name = 'cart_items'
            ) THEN
                ALTER TABLE cart_items 
                ADD CONSTRAINT fk_cart_items_product_id 
                FOREIGN KEY (product_id) REFERENCES products (id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Drop constraint if it exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 
                FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_cart_items_product_id' 
                AND table_name = 'cart_items'
            ) THEN
                ALTER TABLE cart_items 
                DROP CONSTRAINT fk_cart_items_product_id;
            END IF;
        END $$;
    """)
