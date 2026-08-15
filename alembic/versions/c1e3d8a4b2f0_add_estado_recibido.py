"""add_estado_recibido

Ofensiva 1 / Misión 2 — Cierre del ciclo de compras.

Añade el estado 'RECIBIDO' al enum nativo PG `estadorequerimiento`. Tras recibir
la compra global (POST /recibir), los requerimientos PENDIENTE/CONSOLIDADO
transicionan a RECIBIDO.

Revision ID: c1e3d8a4b2f0
Revises: fd9667ee8b81
Create Date: 2026-08-13 17:00:00

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c1e3d8a4b2f0'
down_revision: Union[str, Sequence[str], None] = 'fd9667ee8b81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PG (ENVIRONMENT=production): añade el valor al enum nativo sin tocar filas.
    op.execute("ALTER TYPE estadorequerimiento ADD VALUE IF NOT EXISTS 'RECIBIDO'")


def downgrade() -> None:
    # PG no soporta DROP VALUE de un enum; no-op intencional (el valor es inocuo).
    pass
