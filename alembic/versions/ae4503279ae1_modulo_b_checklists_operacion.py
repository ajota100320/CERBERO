"""modulo_b_checklists_operacion

MÓDULO B: Checklists de Operación.

Crea las tablas:
  - plantillas_checklist (multi-tenant: empresa_id)
  - tareas_checklist (hijos de una plantilla)
  - ejecuciones_plantillas (ejecución de una plantilla por sucursal y fecha)

NOTA DE NOMBRE: la clase 'EjecucionPlantilla' respeta el schema pedido por el SOP
(plantilla_id + sucursal_id + fecha_ejecucion + completado). El nombre difiere de
'EjecucionChecklist' porque esa clase ya existe (Fase 4) con tabla
'ejecuciones_checklist' migrada y schema distinto; no se reutiliza para no romper
la BD existente.

Revision ID: ae4503279ae1
Revises: 7749a68a7823
Create Date: 2026-08-14 03:11:58.639349

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae4503279ae1'
down_revision: Union[str, Sequence[str], None] = '7749a68a7823'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('plantillas_checklist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('titulo', sa.String(length=200), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plantillas_checklist_activo'), 'plantillas_checklist', ['activo'], unique=False)
    op.create_index(op.f('ix_plantillas_checklist_empresa_id'), 'plantillas_checklist', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_plantillas_checklist_id'), 'plantillas_checklist', ['id'], unique=False)
    op.create_index(op.f('ix_plantillas_checklist_titulo'), 'plantillas_checklist', ['titulo'], unique=False)
    op.create_table('ejecuciones_plantillas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('plantilla_id', sa.Integer(), nullable=False),
    sa.Column('sucursal_id', sa.Integer(), nullable=False),
    sa.Column('fecha_ejecucion', sa.DateTime(), nullable=False),
    sa.Column('completado', sa.Boolean(), nullable=False),
    sa.Column('observaciones', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
    sa.ForeignKeyConstraint(['plantilla_id'], ['plantillas_checklist.id'], ),
    sa.ForeignKeyConstraint(['sucursal_id'], ['sucursales.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ejecuciones_plantillas_completado'), 'ejecuciones_plantillas', ['completado'], unique=False)
    op.create_index(op.f('ix_ejecuciones_plantillas_empresa_id'), 'ejecuciones_plantillas', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_ejecuciones_plantillas_fecha_ejecucion'), 'ejecuciones_plantillas', ['fecha_ejecucion'], unique=False)
    op.create_index(op.f('ix_ejecuciones_plantillas_id'), 'ejecuciones_plantillas', ['id'], unique=False)
    op.create_index(op.f('ix_ejecuciones_plantillas_plantilla_id'), 'ejecuciones_plantillas', ['plantilla_id'], unique=False)
    op.create_index(op.f('ix_ejecuciones_plantillas_sucursal_id'), 'ejecuciones_plantillas', ['sucursal_id'], unique=False)
    op.create_table('tareas_checklist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('plantilla_id', sa.Integer(), nullable=False),
    sa.Column('descripcion', sa.String(length=300), nullable=False),
    sa.ForeignKeyConstraint(['plantilla_id'], ['plantillas_checklist.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tareas_checklist_id'), 'tareas_checklist', ['id'], unique=False)
    op.create_index(op.f('ix_tareas_checklist_plantilla_id'), 'tareas_checklist', ['plantilla_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_tareas_checklist_plantilla_id'), table_name='tareas_checklist')
    op.drop_index(op.f('ix_tareas_checklist_id'), table_name='tareas_checklist')
    op.drop_table('tareas_checklist')
    op.drop_index(op.f('ix_ejecuciones_plantillas_sucursal_id'), table_name='ejecuciones_plantillas')
    op.drop_index(op.f('ix_ejecuciones_plantillas_plantilla_id'), table_name='ejecuciones_plantillas')
    op.drop_index(op.f('ix_ejecuciones_plantillas_id'), table_name='ejecuciones_plantillas')
    op.drop_index(op.f('ix_ejecuciones_plantillas_fecha_ejecucion'), table_name='ejecuciones_plantillas')
    op.drop_index(op.f('ix_ejecuciones_plantillas_empresa_id'), table_name='ejecuciones_plantillas')
    op.drop_index(op.f('ix_ejecuciones_plantillas_completado'), table_name='ejecuciones_plantillas')
    op.drop_table('ejecuciones_plantillas')
    op.drop_index(op.f('ix_plantillas_checklist_titulo'), table_name='plantillas_checklist')
    op.drop_index(op.f('ix_plantillas_checklist_id'), table_name='plantillas_checklist')
    op.drop_index(op.f('ix_plantillas_checklist_empresa_id'), table_name='plantillas_checklist')
    op.drop_index(op.f('ix_plantillas_checklist_activo'), table_name='plantillas_checklist')
    op.drop_table('plantillas_checklist')
