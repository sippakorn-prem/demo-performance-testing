"""Fix cart_items sequence

Revision ID: 003_fix_sequence
Revises: 002_add_fk
Create Date: 2026-01-27 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_fix_sequence'
down_revision: Union[str, None] = '002_add_fk'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix cart_items sequence to start from max(id) + 1
    # This ensures auto-increment works correctly even if data was seeded manually
    op.execute("""
        DO $$
        DECLARE
            max_id INTEGER;
        BEGIN
            -- Get the maximum ID from cart_items
            SELECT COALESCE(MAX(id), 0) INTO max_id FROM cart_items;
            
            -- Create sequence if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM pg_sequences WHERE sequencename = 'cart_items_id_seq'
            ) THEN
                CREATE SEQUENCE cart_items_id_seq;
            END IF;
            
            -- Set the sequence to start from max_id + 1
            PERFORM setval('cart_items_id_seq', GREATEST(max_id, 1), true);
            
            -- Set the default value for the id column to use the sequence
            ALTER TABLE cart_items 
            ALTER COLUMN id SET DEFAULT nextval('cart_items_id_seq');
        END $$;
    """)


def downgrade() -> None:
    # Remove the default and sequence (optional, can be left as is)
    op.execute("ALTER TABLE cart_items ALTER COLUMN id DROP DEFAULT")
