"""add_unidades_medida_tabla_multitenant

Crea la tabla multi-tenant 'unidades_medida' (modelo UnidadMedidaTabla).

NOTA (editada manualmente): el autogenerate original incluyó columnas enum
de modelos Fase 4 (alertas, incidencias, capacitaciones_usuarios,
ejecuciones_checklist) que NUNCA se migraron a prod — drift pre-existente
FUERA DE ALCANCE y peligroso (NOT NULL sobre tablas pobladas). Se eliminaron.
SOLO se crea 'unidades_medida'.

Revision ID: fb9a58546452
Revises: e1f3e5e91cc8
Create Date: 2026-08-12 03:31:39.749934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb9a58546452'
down_revision: Union[str, Sequence[str], None] = 'e1f3e5e91cc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: solo crea la tabla unidades_medida (multi-tenant)."""
    op.create_table('unidades_medida',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('abreviatura', sa.String(length=20), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_unidades_medida_abreviatura'), 'unidades_medida', ['abreviatura'], unique=False)
    op.create_index(op.f('ix_unidades_medida_activo'), 'unidades_medida', ['activo'], unique=False)
    op.create_index(op.f('ix_unidades_medida_empresa_id'), 'unidades_medida', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_unidades_medida_id'), 'unidades_medida', ['id'], unique=False)
    op.create_index(op.f('ix_unidades_medida_nombre'), 'unidades_medida', ['nombre'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_unidades_medida_nombre'), table_name='unidades_medida')
    op.drop_index(op.f('ix_unidades_medida_id'), table_name='unidades_medida')
    op.drop_index(op.f('ix_unidades_medida_empresa_id'), table_name='unidades_medida')
    op.drop_index(op.f('ix_unidades_medida_activo'), table_name='unidades_medida')
    op.drop_index(op.f('ix_unidades_medida_abreviatura'), table_name='unidades_medida')
    op.drop_table('unidades_medida')
