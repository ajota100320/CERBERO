"""Añade columna debe_cambiar_password a la tabla usuarios

Revision ID: 9b80c4d8f1a3
Revises: 7e5f5f9231a2
Create Date: 2026-08-07

SEGURIDAD PRIMER INGRESO:
- Nuevos usuarios creados por SuperAdmin/Admin nacen con
  debe_cambiar_password=True (default ORM).
- EXISTENTES: server_default='false' ⇒ todos quedan en False
  (incluido SuperAdmin y admin@erp.cl).
- require_auth fuerza redirect a /cambiar-password si flag=True.
- Tras cambio de clave, flag → False + sesión rotada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9b80c4d8f1a3'
down_revision: Union[str, Sequence[str], None] = '7e5f5f9231a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column(
            "debe_cambiar_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("usuarios", "debe_cambiar_password")