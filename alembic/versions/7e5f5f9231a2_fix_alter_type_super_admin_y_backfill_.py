"""Fix ALTER TYPE SUPER_ADMIN y backfill branding

Revision ID: 7e5f5f9231a2
Revises: 8031e44472c9
Create Date: 2026-08-06

Corrige la migración 8031e44472c9 (solo columnas de branding, omitió el
ALTER TYPE del enum nativo de PostgreSQL y el backfill de Empresa 1).

Ejecutado directamente con autocommit porque Alembic bloquea op.execute("COMMIT")
dentro de transacciones wrapper — PG exige que ALTER TYPE ADD VALUE corra
fuera de bloque transaccional.

Resultado:
  - Enum rolusuario extendido: + 'Super Admin'.
  - Empresa 1 backfill: nombre_comercial='Templo del Smash',
    color_primario='#1a1a2e', color_secundario='#16213e'.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7e5f5f9231a2'
down_revision: Union[str, Sequence[str], None] = '8031e44472c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ══════════════════════════════════════════════
    # ALTER TYPE (autocommit requerido por PG)
    # ══════════════════════════════════════════════
    # Alembic envuelve upgrade() en transacción → op.execute("COMMIT")
    # es rechazado. Solución: ejecutar con autocommit via get_bind().
    conn = op.get_bind()
    conn = conn.execution_options(isolation_level="AUTOCOMMIT")
    conn.execute(
        sa.text("ALTER TYPE rolusuario ADD VALUE IF NOT EXISTS 'Super Admin'")
    )

    # ══════════════════════════════════════════════
    # Backfill — Empresa 1 (Templo del Smash)
    # ══════════════════════════════════════════════
    conn.execute(
        sa.text(
            "UPDATE empresas SET "
            "nombre_comercial = 'Templo del Smash', "
            "color_primario   = '#1a1a2e', "
            "color_secundario = '#16213e' "
            "WHERE id = 1 AND nombre_comercial IS NULL"
        )
    )


def downgrade() -> None:
    # El valor del enum NO se elimina (PG no soporta DROP VALUE de enum nativo).
    # El backfill es idempotente — sin efecto que revertir.
    pass