"""Setup Multi-Tenant

Revision ID: a006e679678a
Revises: 503d5a1c2297
Create Date: 2026-08-06 02:53:00.273606

Estructurada en 3 FASES (a prueba de constraints en PostgreSQL):

  FASE A: crear tabla `empresas` + añadir columna empresa_id NULLABLE
  FASE B: seed Empresa "Templo del Smash" (id=1) + UPDATE backfill de
          las 22 filas existentes → empresa_id = 1  (Zero Data Loss)
  FASE C: alterar empresa_id a NOT NULL + FKs con nombre explícito

IDEMPOTENTE: todos los DDL usan IF NOT EXISTS para tolerar ejecuciones
parciales (p. ej. si un primer intento dejó la tabla `empresas` creada
pero falló antes de registrar la revisión).

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a006e679678a'
down_revision: Union[str, Sequence[str], None] = '503d5a1c2297'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tablas de negocio que reciben la columna empresa_id (13)
TABLAS_TENANT = [
    'control_gastos',
    'detalle_compras',
    'higiene_personal',
    'ingredientes_stock',
    'lista_verificacion_diario',
    'notificaciones',
    'proveedores',
    'registro_compras',
    'registro_mermas',
    'registro_temperaturas',
    'requerimientos',
    'sucursales',
    'usuarios',
]


def upgrade() -> None:
    """Upgrade schema."""
    # ══════════════════════════════════════════════
    # FASE A: tabla Empresas + columna NULLABLE
    # ══════════════════════════════════════════════
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS empresas (
                id          INTEGER PRIMARY KEY,
                nombre      VARCHAR(150) NOT NULL,
                rut         VARCHAR(20) NOT NULL UNIQUE,
                plan        VARCHAR(20) NOT NULL DEFAULT 'basic',
                activa      BOOLEAN NOT NULL DEFAULT true,
                created_at  TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
                updated_at  TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
            )
            """
        )
    )

    # Columna empresa_id NULLABLE primero (las filas existentes aún no tienen tenant)
    for tabla in TABLAS_TENANT:
        op.execute(
            sa.text(
                f"ALTER TABLE {tabla} ADD COLUMN IF NOT EXISTS empresa_id INTEGER"
            )
        )
        op.execute(
            sa.text(
                f"CREATE INDEX IF NOT EXISTS ix_{tabla}_empresa_id ON {tabla} (empresa_id)"
            )
        )

    # ══════════════════════════════════════════════
    # FASE B: Seed empresa fundadora + backfill de datos
    # ══════════════════════════════════════════════
    # Empresa "Templo del Smash" ocupa el id=1 → todos los registros históricos
    # (2 sucursales, 6 usuarios, 4 proveedores, 8 ingredientes, 2 notificaciones
    #  = 22 filas) quedan asignados a ella. Zero Data Loss.
    op.execute(
        sa.text(
            "INSERT INTO empresas (id, nombre, rut, plan, activa) "
            "VALUES (1, 'Templo del Smash', '76.123.456-7', 'enterprise', true) "
            "ON CONFLICT (id) DO NOTHING"
        )
    )

    for tabla in TABLAS_TENANT:
        op.execute(
            sa.text(
                f"UPDATE {tabla} SET empresa_id = 1 WHERE empresa_id IS NULL"
            )
        )

    # ══════════════════════════════════════════════
    # FASE C: NOT NULL + FKs con nombre explícito
    # ══════════════════════════════════════════════
    for tabla in TABLAS_TENANT:
        op.execute(
            sa.text(
                f"ALTER TABLE {tabla} ALTER COLUMN empresa_id SET NOT NULL"
            )
        )
        # PostgreSQL no soporta ADD CONSTRAINT IF NOT EXISTS; las FKs solo se
        # crean aquí (esta fase nunca se ejecutó en intentos previos).
        op.execute(
            sa.text(
                f"ALTER TABLE {tabla} ADD CONSTRAINT fk_{tabla}_empresa "
                f"FOREIGN KEY (empresa_id) REFERENCES empresas (id)"
            )
        )


def downgrade() -> None:
    """Downgrade schema."""
    # FKs con nombre explícito (el autogenerate ponía None → fallaba en PG)
    for tabla in TABLAS_TENANT:
        op.execute(
            sa.text(
                f"ALTER TABLE {tabla} DROP CONSTRAINT IF EXISTS fk_{tabla}_empresa"
            )
        )
        op.execute(
            sa.text(f"DROP INDEX IF EXISTS ix_{tabla}_empresa_id")
        )
        op.execute(
            sa.text(f"ALTER TABLE {tabla} DROP COLUMN IF EXISTS empresa_id")
        )

    # La empresa fundadora se elimina (las tablas ya no la referencian)
    op.execute(sa.text("DELETE FROM empresas WHERE id = 1"))
    op.execute(sa.text("DROP TABLE IF EXISTS empresas"))
