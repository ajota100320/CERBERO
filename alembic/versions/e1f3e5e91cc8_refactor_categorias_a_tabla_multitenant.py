"""Refactor categorias a tabla multitenant

Convierte el enum fijo CategoriaIngrediente en la tabla editable
categorias_insumos (multi-tenant) y migra los datos existentes.

Revision ID: e1f3e5e91cc8
Revises: f8d3f71b6754
Create Date: 2026-08-12 02:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f3e5e91cc8'
down_revision: Union[str, Sequence[str], None] = 'f8d3f71b6754'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Mapeo enum CategoriaIngrediente -> nombre de categoría editable
DEFAULT_CATEGORIAS = [
    ("CARNES", "Carnes", "Carnes rojas, blancas y embutidos"),
    ("VERDURAS", "Verduras", "Hortalizas y verduras frescas"),
    ("FRUTAS", "Frutas", "Frutas frescas"),
    ("LACTEOS", "Lácteos", "Lácteos y derivados"),
    ("GRANOS", "Granos y Cereales", "Arroz, legumbres y cereales"),
    ("CONDIMENTOS", "Condimentos", "Especias y condimentos"),
    ("BEBIDAS", "Bebidas", "Bebidas y jugos"),
    ("OTROS", "Otros", "Otros insumos"),
]


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Crear la tabla categorias_insumos (multi-tenant)
    op.create_table('categorias_insumos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=150), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_categorias_insumos_activo'), 'categorias_insumos', ['activo'], unique=False)
    op.create_index(op.f('ix_categorias_insumos_empresa_id'), 'categorias_insumos', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_categorias_insumos_id'), 'categorias_insumos', ['id'], unique=False)
    op.create_index(op.f('ix_categorias_insumos_nombre'), 'categorias_insumos', ['nombre'], unique=False)

    # 2. Añadir columna categoria_id (nullable para poder migrar)
    op.add_column('ingredientes_stock', sa.Column('categoria_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_ingredientes_stock_categoria_id'), 'ingredientes_stock', ['categoria_id'], unique=False)
    op.create_foreign_key('fk_ingredientes_stock_categoria_id', 'ingredientes_stock', 'categorias_insumos', ['categoria_id'], ['id'])

    # 3. Backfill: sembrar categorías por empresa y mapear el enum a categoria_id
    conn = op.get_bind()
    # Para cada empresa, crear las categorías por defecto y guardar mapping enum->id
    empresas = conn.execute(sa.text("SELECT id FROM empresas")).fetchall()
    for (empresa_id,) in empresas:
        mapping = {}
        for enum_val, nombre, descripcion in DEFAULT_CATEGORIAS:
            cat_id = conn.execute(
                sa.text(
                    "INSERT INTO categorias_insumos (nombre, descripcion, activo, empresa_id) "
                    "VALUES (:n, :d, :a, :e) RETURNING id"
                ),
                {"n": nombre, "d": descripcion, "a": True, "e": empresa_id}
            ).scalar()
            mapping[enum_val] = cat_id
        # Migrar cada ingrediente del tenant
        rows = conn.execute(
            sa.text("SELECT id, categoria FROM ingredientes_stock WHERE empresa_id = :e"),
            {"e": empresa_id}
        ).fetchall()
        for ing_id, enum_val in rows:
            if enum_val is None:
                continue
            target_id = mapping.get(str(enum_val)) or mapping.get("OTROS")
            conn.execute(
                sa.text("UPDATE ingredientes_stock SET categoria_id = :cid WHERE id = :iid"),
                {"cid": target_id, "iid": ing_id}
            )

    # 4. Eliminar la columna enum obsoleta (Postgres necesita explicit)
    try:
        op.drop_column('ingredientes_stock', 'categoria')
    except Exception:
        # SQLite no siempre soporta DROP COLUMN; si falla, se mantiene inerte.
        pass


def downgrade() -> None:
    """Downgrade schema."""
    try:
        op.add_column('ingredientes_stock', sa.Column('categoria', sa.Enum(
            'CARNES', 'VERDURAS', 'FRUTAS', 'LACTEOS', 'GRANOS', 'CONDIMENTOS', 'BEBIDAS', 'OTROS',
            name='categoriaingrediente'), nullable=True))
    except Exception:
        pass
    op.drop_constraint('fk_ingredientes_stock_categoria_id', 'ingredientes_stock', type_='foreignkey')
    op.drop_index(op.f('ix_ingredientes_stock_categoria_id'), table_name='ingredientes_stock')
    op.drop_column('ingredientes_stock', 'categoria_id')
    op.drop_index(op.f('ix_categorias_insumos_nombre'), table_name='categorias_insumos')
    op.drop_index(op.f('ix_categorias_insumos_id'), table_name='categorias_insumos')
    op.drop_index(op.f('ix_categorias_insumos_empresa_id'), table_name='categorias_insumos')
    op.drop_index(op.f('ix_categorias_insumos_activo'), table_name='categorias_insumos')
    op.drop_table('categorias_insumos')
