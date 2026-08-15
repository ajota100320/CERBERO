"""modulo_a_rrhh_asistencia

MÓDULO A: Recursos Humanos y Control de Asistencia.

Crea las tablas:
  - empleados (multi-tenant: empresa_id + sucursal_id)
  - turnos_asistencia (reloj de control: entrada/salida por empleado y fecha)

Revision ID: 7749a68a7823
Revises: a7b2c3d4e5f6
Create Date: 2026-08-14 03:04:34.175263

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7749a68a7823'
down_revision: Union[str, Sequence[str], None] = 'a7b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('empleados',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(length=150), nullable=False),
    sa.Column('cargo', sa.String(length=100), nullable=True),
    sa.Column('sucursal_id', sa.Integer(), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
    sa.ForeignKeyConstraint(['sucursal_id'], ['sucursales.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_empleados_activo'), 'empleados', ['activo'], unique=False)
    op.create_index(op.f('ix_empleados_cargo'), 'empleados', ['cargo'], unique=False)
    op.create_index(op.f('ix_empleados_empresa_id'), 'empleados', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_empleados_id'), 'empleados', ['id'], unique=False)
    op.create_index(op.f('ix_empleados_nombre'), 'empleados', ['nombre'], unique=False)
    op.create_index(op.f('ix_empleados_sucursal_id'), 'empleados', ['sucursal_id'], unique=False)
    op.create_table('turnos_asistencia',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('empleado_id', sa.Integer(), nullable=False),
    sa.Column('fecha', sa.Date(), nullable=False),
    sa.Column('hora_entrada', sa.DateTime(), nullable=True),
    sa.Column('hora_salida', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['empleado_id'], ['empleados.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_turnos_asistencia_empleado_id'), 'turnos_asistencia', ['empleado_id'], unique=False)
    op.create_index(op.f('ix_turnos_asistencia_fecha'), 'turnos_asistencia', ['fecha'], unique=False)
    op.create_index(op.f('ix_turnos_asistencia_id'), 'turnos_asistencia', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_turnos_asistencia_id'), table_name='turnos_asistencia')
    op.drop_index(op.f('ix_turnos_asistencia_fecha'), table_name='turnos_asistencia')
    op.drop_index(op.f('ix_turnos_asistencia_empleado_id'), table_name='turnos_asistencia')
    op.drop_table('turnos_asistencia')
    op.drop_index(op.f('ix_empleados_sucursal_id'), table_name='empleados')
    op.drop_index(op.f('ix_empleados_nombre'), table_name='empleados')
    op.drop_index(op.f('ix_empleados_id'), table_name='empleados')
    op.drop_index(op.f('ix_empleados_empresa_id'), table_name='empleados')
    op.drop_index(op.f('ix_empleados_cargo'), table_name='empleados')
    op.drop_index(op.f('ix_empleados_activo'), table_name='empleados')
    op.drop_table('empleados')
