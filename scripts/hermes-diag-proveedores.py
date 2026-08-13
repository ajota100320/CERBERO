"""Diagnóstico read-only: motor activo, conectividad, alembic head, tablas proveedores/unidades_medida.
NUNCA imprime credenciales. Uso: python hermes-diag-proveedores.py
"""
import sys, os, re

# Asegurar raíz del proyecto en path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, PROJECT_ROOT)

from app import database  # importa modelos y resuelve DATABASE_URL
from app.database import engine, Base

def mask(url: str) -> str:
    # postgresql://user:pw@host/db -> postgresql://user:***@host/db
    m = re.match(r"^(postgresql(?:\+\w+)?://)([^:]+):([^@]+)@(.*)$", url)
    if m:
        return f"{m.group(1)}{m.group(2)}:***@{m.group(4)}"
    return url

print("=" * 60)
print("DIAGNÓSTICO READ-ONLY")
print("=" * 60)
print(f"ENVIRONMENT      : {database.ENVIRONMENT}")
print(f"Motor activo     : {'PostgreSQL' if database.ENVIRONMENT == 'production' else 'SQLite'}")
print(f"DATABASE_URL     : {mask(database.DATABASE_URL)}")

# 1) Conectividad + tablas existentes
from sqlalchemy import inspect
try:
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    print("\n[CONECTIVIDAD] OK - conexión establecida")
    print(f"  total tablas   : {len(tables)}")
    print(f"  proveedores    : {'EXISTE' if 'proveedores' in tables else 'NO EXISTE'}")
    print(f"  unidades_medida: {'EXISTE' if 'unidades_medida' in tables else 'NO EXISTE'}")
    print(f"  categorias_insumos: {'EXISTE' if 'categorias_insumos' in tables else 'NO EXISTE'}")
    # Proveedor: columnas reales
    if 'proveedores' in tables:
        cols = [c['name'] for c in insp.get_columns('proveedores')]
        print(f"  proveedores columnas: {cols}")
except Exception as e:
    print(f"\n[CONECTIVIDAD] FALLO: {type(e).__name__}: {e}")

# 2) Estado Alembic: head y versión aplicada en BD
print("\n[ALEMBIC]")
try:
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext

    cfg = Config(os.path.join(PROJECT_ROOT, "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    print(f"  heads en disco    : {heads}")

    with engine.connect() as conn:
        mc = MigrationContext.configure(conn)
        current = mc.get_current_heads()
    print(f"  version aplicada  : {current}")
    if heads == current:
        print("  ESTADO           : SÍNCRONO (head aplicado)")
    else:
        print("  ESTADO           : DESINCRONIZADO -> se requiere upgrade head")
except Exception as e:
    print(f"  FALLO: {type(e).__name__}: {e}")

# 3) Proveedor: ¿tiene filas en prod? (solo COUNT, sin datos)
print("\n[DATOS PROVEEDOR]")
try:
    from app.database import Proveedor
    from sqlalchemy import func
    with engine.connect() as conn:
        cnt = conn.execute(func.count().select().select_from(Proveedor.__table__)).scalar()
    print(f"  filas en proveedores: {cnt}")
except Exception as e:
    print(f"  FALLO: {type(e).__name__}: {e}")

print("\n[FIN DIAGNÓSTICO]")
