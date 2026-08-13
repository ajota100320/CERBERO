"""add_requerimientos_multi_sucursal

Motor de Requerimientos Multi-Sucursal y Consolidación (Misión 1).

Remodela la tabla `requerimientos` (legacy: producto/cantidad/precio/prioridad,
VACÍA en prod) al esquema jerárquico multi-tenant:
  Requerimiento   -> sucursal_id, fecha_solicitud, estado, usuario_id, empresa_id
  DetalleRequerimiento -> requerimiento_id, insumo_id, cantidad_solicitada

Como la tabla legacy `requerimientos` no tiene filas, se dropea y recrea con el
nuevo esquema. Se crea el enum nativo PG `estadorequerimiento` y la tabla
`detalle_requerimientos`. NO se tocan modelos Fase4 (drift pre-existente FUERA
de alcance).

Revision ID: fd9667ee8b81
Revises: fb9a58546452
Create Date: 2026-08-13 16:37:29.319208

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd9667ee8b81'
down_revision: Union[str, Sequence[str], None] = 'fb9a58546452'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: remodela requerimientos + crea detalle_requerimientos."""
    # 1. DROP de la tabla legacy (VACÍA en prod) y su índice.
    op.drop_index(op.f('ix_requerimientos_empresa_id'), table_name='requerimientos')
    op.drop_index(op.f('ix_requerimientos_id'), table_name='requerimientos')
    op.drop_table('requerimientos')

    # 2. Enum nativo PG para el estado (lo crea create_table automáticamente).
    estado_enum = sa.Enum('PENDIENTE', 'CONSOLIDADO', 'COMPRADO', name='estadorequerimiento')

    # 3. Recrear `requerimientos` con el nuevo esquema multi-tenant jerárquico.
    op.create_table('requerimientos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sucursal_id', sa.Integer(), nullable=False),
    sa.Column('fecha_solicitud', sa.DateTime(), nullable=False),
    sa.Column('estado', estado_enum, nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
    sa.ForeignKeyConstraint(['sucursal_id'], ['sucursales.id'], ),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_requerimientos_empresa_id'), 'requerimientos', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_requerimientos_estado'), 'requerimientos', ['estado'], unique=False)
    op.create_index(op.f('ix_requerimientos_fecha_solicitud'), 'requerimientos', ['fecha_solicitud'], unique=False)
    op.create_index(op.f('ix_requerimientos_id'), 'requerimientos', ['id'], unique=False)
    op.create_index(op.f('ix_requerimientos_sucursal_id'), 'requerimientos', ['sucursal_id'], unique=False)

    # 4. Tabla de detalle (líneas por insumo).
    op.create_table('detalle_requerimientos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('requerimiento_id', sa.Integer(), nullable=False),
    sa.Column('insumo_id', sa.Integer(), nullable=False),
    sa.Column('cantidad_solicitada', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['insumo_id'], ['ingredientes_stock.id'], ),
    sa.ForeignKeyConstraint(['requerimiento_id'], ['requerimientos.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detalle_requerimientos_id'), 'detalle_requerimientos', ['id'], unique=False)
    op.create_index(op.f('ix_detalle_requerimientos_insumo_id'), 'detalle_requerimientos', ['insumo_id'], unique=False)
    op.create_index(op.f('ix_detalle_requerimientos_requerimiento_id'), 'detalle_requerimientos', ['requerimiento_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema: restaura esquema legacy (vacío)."""
    op.drop_index(op.f('ix_detalle_requerimientos_requerimiento_id'), table_name='detalle_requerimientos')
    op.drop_index(op.f('ix_detalle_requerimientos_insumo_id'), table_name='detalle_requerimientos')
    op.drop_index(op.f('ix_detalle_requerimientos_id'), table_name='detalle_requerimientos')
    op.drop_table('detalle_requerimientos')

    op.drop_index(op.f('ix_requerimientos_sucursal_id'), table_name='requerimientos')
    op.drop_index(op.f('ix_requerimientos_id'), table_name='requerimientos')
    op.drop_index(op.f('ix_requerimientos_fecha_solicitud'), table_name='requerimientos')
    op.drop_index(op.f('ix_requerimientos_estado'), table_name='requerimientos')
    op.drop_index(op.f('ix_requerimientos_empresa_id'), table_name='requerimientos')
    op.drop_table('requerimientos')

    sa.Enum('PENDIENTE', 'CONSOLIDADO', 'COMPRADO', name='estadorequerimiento').drop(op.get_bind(), checkfirst=True)

    # Restaurar tabla legacy (esquema fase 1).
    op.create_table('requerimientos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('producto', sa.String(length=200), nullable=False),
    sa.Column('cantidad', sa.Float(), nullable=False),
    sa.Column('precio_estimado', sa.Float(), nullable=False),
    sa.Column('prioridad', sa.Enum('ALTA', 'MEDIA', 'BAJA', name='prioridad'), nullable=False),
    sa.Column('sucursal_id', sa.Integer(), nullable=False),
    sa.Column('fecha_registro', sa.DateTime(), nullable=True),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
    sa.ForeignKeyConstraint(['sucursal_id'], ['sucursales.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_requerimientos_id'), 'requerimientos', ['id'], unique=False)
    op.create_index(op.f('ix_requerimientos_empresa_id'), 'requerimientos', ['empresa_id'], unique=False)
