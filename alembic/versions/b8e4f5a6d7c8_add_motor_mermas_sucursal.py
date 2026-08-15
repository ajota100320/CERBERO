"""add_motor_mermas_sucursal

FASE 5 (Control de Fugas) — Motor Backend de Mermas.

Añade la columna `sucursal_id` a `registro_mermas` para que cada merma quede
vinculada a la sucursal donde ocurrió (multi-sucursal jerárquico). Esto permite
el filtrado obligatorio GET por empresa_id + sucursal_id de la Regla 5.

ADD COLUMN aditiva y reversible (no destructiva).

Revision ID: b8e4f5a6d7c8
Revises: a7b2c3d4e5f6
Create Date: 2026-08-14 18:45:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8e4f5a6d7c8'
down_revision: Union[str, Sequence[str], None] = 'ae4503279ae1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Añade sucursal_id a registro_mermas (nullable, index)."""
    op.add_column(
        'registro_mermas',
        sa.Column('sucursal_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_registro_mermas_sucursal',
        'registro_mermas',
        'sucursales',
        ['sucursal_id'],
        ['id'],
    )
    op.create_index(
        op.f('ix_registro_mermas_sucursal_id'),
        'registro_mermas',
        ['sucursal_id'],
        unique=False,
    )


def downgrade() -> None:
    """Revoca sucursal_id de registro_mermas."""
    op.drop_index(op.f('ix_registro_mermas_sucursal_id'), table_name='registro_mermas')
    op.drop_constraint('fk_registro_mermas_sucursal', 'registro_mermas', type_='foreignkey')
    op.drop_column('registro_mermas', 'sucursal_id')
