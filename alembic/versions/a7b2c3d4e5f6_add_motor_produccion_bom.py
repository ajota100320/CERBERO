"""add_motor_produccion_bom

Motor de Producción (BOM - Bill of Materials) — Misión 1.

Crea el esquema jerárquico de fichas técnicas multi-tenant:
  recetas                -> nombre, descripcion, rendimiento_base, empresa_id
  detalle_recetas        -> receta_id, insumo_id, cantidad_necesaria
  historial_produccion   -> receta_id, sucursal_id, cantidad_producida,
                            costo_total_calculado, fecha, usuario_id

Solo crea las 3 tablas nuevas (sin tocar modelos Fase 4 — drift pre-existente
FUERA de alcance). Sin enums nuevos.

Revision ID: a7b2c3d4e5f6
Revises: c1e3d8a4b2f0
Create Date: 2026-08-14 01:45:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'c1e3d8a4b2f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea las tablas del Motor de Producción (BOM)."""
    # 1. Recetas (fichas técnicas maestras por empresa).
    op.create_table(
        'recetas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=200), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('rendimiento_base', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_recetas_empresa_id'), 'recetas', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_recetas_id'), 'recetas', ['id'], unique=False)
    op.create_index(op.f('ix_recetas_nombre'), 'recetas', ['nombre'], unique=False)

    # 2. DetalleReceta (insumos por receta).
    op.create_table(
        'detalle_recetas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('receta_id', sa.Integer(), nullable=False),
        sa.Column('insumo_id', sa.Integer(), nullable=False),
        sa.Column('cantidad_necesaria', sa.Float(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
        sa.ForeignKeyConstraint(['insumo_id'], ['ingredientes_stock.id'], ),
        sa.ForeignKeyConstraint(['receta_id'], ['recetas.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_detalle_recetas_empresa_id'), 'detalle_recetas', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_detalle_recetas_id'), 'detalle_recetas', ['id'], unique=False)
    op.create_index(op.f('ix_detalle_recetas_insumo_id'), 'detalle_recetas', ['insumo_id'], unique=False)
    op.create_index(op.f('ix_detalle_recetas_receta_id'), 'detalle_recetas', ['receta_id'], unique=False)

    # 3. HistorialProduccion (ejecuciones reales).
    op.create_table(
        'historial_produccion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('receta_id', sa.Integer(), nullable=False),
        sa.Column('sucursal_id', sa.Integer(), nullable=False),
        sa.Column('cantidad_producida', sa.Float(), nullable=False),
        sa.Column('costo_total_calculado', sa.Float(), nullable=False),
        sa.Column('fecha', sa.DateTime(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
        sa.ForeignKeyConstraint(['receta_id'], ['recetas.id'], ),
        sa.ForeignKeyConstraint(['sucursal_id'], ['sucursales.id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_historial_produccion_empresa_id'), 'historial_produccion', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_historial_produccion_fecha'), 'historial_produccion', ['fecha'], unique=False)
    op.create_index(op.f('ix_historial_produccion_id'), 'historial_produccion', ['id'], unique=False)
    op.create_index(op.f('ix_historial_produccion_receta_id'), 'historial_produccion', ['receta_id'], unique=False)
    op.create_index(op.f('ix_historial_produccion_sucursal_id'), 'historial_produccion', ['sucursal_id'], unique=False)


def downgrade() -> None:
    """Elimina las tablas del Motor de Producción."""
    op.drop_index(op.f('ix_historial_produccion_sucursal_id'), table_name='historial_produccion')
    op.drop_index(op.f('ix_historial_produccion_receta_id'), table_name='historial_produccion')
    op.drop_index(op.f('ix_historial_produccion_id'), table_name='historial_produccion')
    op.drop_index(op.f('ix_historial_produccion_fecha'), table_name='historial_produccion')
    op.drop_index(op.f('ix_historial_produccion_empresa_id'), table_name='historial_produccion')
    op.drop_table('historial_produccion')

    op.drop_index(op.f('ix_detalle_recetas_receta_id'), table_name='detalle_recetas')
    op.drop_index(op.f('ix_detalle_recetas_insumo_id'), table_name='detalle_recetas')
    op.drop_index(op.f('ix_detalle_recetas_id'), table_name='detalle_recetas')
    op.drop_index(op.f('ix_detalle_recetas_empresa_id'), table_name='detalle_recetas')
    op.drop_table('detalle_recetas')

    op.drop_index(op.f('ix_recetas_nombre'), table_name='recetas')
    op.drop_index(op.f('ix_recetas_id'), table_name='recetas')
    op.drop_index(op.f('ix_recetas_empresa_id'), table_name='recetas')
    op.drop_table('recetas')
