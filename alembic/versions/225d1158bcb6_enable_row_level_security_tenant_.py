"""Enable Row Level Security (tenant isolation LGPD)

Revision ID: 225d1158bcb6
Revises: a006e679678a
Create Date: 2026-08-06 (auto)

CAPA 3 DE DEFENSA EN PROFUNDIDAD — Row Level Security en PostgreSQL.
Activa RLS en las 13 tablas tenant‑aware con una política que respeta
la variable de sesión `app.empresa_id`.

DECISIÓN DE ARQUITECTURA (CTO):
  La capa PRIMARIA de aislamiento es el listener SQLAlchemy (app/tenant.py),
  que filtra por tenant_context (ContextVar inyectado desde el JWT).
  RLS es la CAPA 3 (red de seguridad), activada hoy pero en modo permisivo:
  - Si `app.empresa_id` NO está seteada (NULL, el caso actual de la app
    porque SQLAlchemy pooling hace complejo setearla por conexión) → permite
    todo el acceso. La app no se rompe.
  - Si la variable está seteada → filtra por empresa_id. Esto endurece el
    acceso vía API de Supabase (roles authenticated/anon) cuando en la Fase 2
    configuremos pool‑level session variables.
  El rol `postgres` (superuser, usado por la app) bypassa RLS por defecto.
  El rol `service_role` de Supabase también.

POLÍTICA POR TABLA:
  USING (current_setting('app.empresa_id', true) IS NULL
         OR empresa_id = current_setting('app.empresa_id', true)::int)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '225d1158bcb6'
down_revision: Union[str, Sequence[str], None] = 'a006e679678a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLAS_CON_RLS = [
    "control_gastos",
    "detalle_compras",
    "higiene_personal",
    "ingredientes_stock",
    "lista_verificacion_diario",
    "notificaciones",
    "proveedores",
    "registro_compras",
    "registro_mermas",
    "registro_temperaturas",
    "requerimientos",
    "sucursales",
    "usuarios",
]

POLITICA_SQL = (
    "current_setting('app.empresa_id', true) IS NULL "
    "OR empresa_id = current_setting('app.empresa_id', true)::int"
)


def upgrade() -> None:
    """Enable RLS + policies on all tenant‑aware tables."""
    for tabla in TABLAS_CON_RLS:
        op.execute(sa.text(f"ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY"))
        op.execute(
            sa.text(
                f"CREATE POLICY tenant_isolation_{tabla} ON {tabla} "
                f"USING ({POLITICA_SQL})"
            )
        )


def downgrade() -> None:
    """Remove RLS policies and disable RLS."""
    for tabla in reversed(TABLAS_CON_RLS):
        op.execute(
            sa.text(f"DROP POLICY IF EXISTS tenant_isolation_{tabla} ON {tabla}")
        )
        op.execute(
            sa.text(f"ALTER TABLE {tabla} DISABLE ROW LEVEL SECURITY")
        )