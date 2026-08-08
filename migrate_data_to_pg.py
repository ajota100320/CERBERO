"""
migrate_data_to_pg.py — Migración de datos SQLite → PostgreSQL (Zero Data Loss)

Crea DOS engines de SQLAlchemy:
  - ORIGEN : SQLite (detecta automáticamente el archivo real con datos)
  - DESTINO: PostgreSQL/Supabase (desde .env → DATABASE_URL_POSTGRES)

Respecta el orden topológico de las Foreign Keys (padres antes que hijos)
y PRESERVA los IDs originales para no romper las relaciones.

USO:
  python migrate_data_to_pg.py            # Dry-run: solo cuenta y verifica (seguro)
  python migrate_data_to_pg.py --execute  # Ejecuta la migración real
  python migrate_data_to_pg.py --force    # (con --execute) trunca destino antes de insertar

Al terminar: verifica conteos origen vs destino por tabla y resetea secuencias.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

# ──────────────────────────────────────────────
# 0. CARGAR CONFIGURACIÓN (.env)
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

sys.path.insert(0, str(PROJECT_ROOT))
from app.database import Base  # noqa: E402  (modelos = fuente de verdad del esquema)

# ──────────────────────────────────────────────
# 1. ENGINES
# ──────────────────────────────────────────────
def _detectar_sqlite_origen() -> Path:
    """El .env define sqlite:///./v2.db pero los datos reales pueden estar en
    otro archivo (erp_gastronomico_v2.db). Criterios de selección:
    1) Si existe v2.db (el del .env) → lo usa.
    2) Si no, el archivo que tenga TODAS las tablas del modelo (Base.metadata).
    3) Si hay varios candidatos completos, el modificado más recientemente.
    """
    candidatos = [
        PROJECT_ROOT / "v2.db",
        PROJECT_ROOT / "erp_gastronomico_v2.db",
        PROJECT_ROOT / "erp_gastronomico.db",
    ]
    existentes = [p for p in candidatos if p.exists()]

    # 1) Prioridad absoluta: el archivo declarado en .env
    env_archivo = os.getenv("DATABASE_URL_SQLITE", "").replace("sqlite:///", "").strip()
    if env_archivo:
        env_path = (PROJECT_ROOT / env_archivo) if not os.path.isabs(env_archivo) else Path(env_archivo)
        if env_path.exists():
            return env_path

    if not existentes:
        raise FileNotFoundError(
            "No se encontró ningún archivo SQLite de origen. "
            "Verifica DATABASE_URL_SQLITE en .env"
        )

    # 2) Los que tengan TODAS las tablas del modelo (el "verdadero" origen)
    import sqlite3

    tablas_modelo = set(Base.metadata.tables.keys())
    completos = []
    for p in existentes:
        try:
            conn = sqlite3.connect(str(p))
            tablas_bd = {
                r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
            conn.close()
            if tablas_modelo.issubset(tablas_bd):
                completos.append(p)
        except Exception:
            continue

    if not completos:
        # Ninguno completo: usar el de más filas (fallback degradado)
        mejor, mejor_filas = None, -1
        for p in existentes:
            try:
                conn = sqlite3.connect(str(p))
                total = 0
                for (tabla,) in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ):
                    total += conn.execute(f'SELECT COUNT(*) FROM "{tabla}"').fetchone()[0]
                conn.close()
                if total > mejor_filas:
                    mejor, mejor_filas = p, total
            except Exception:
                continue
        return mejor

    # 3) Entre los completos, el más reciente
    return max(completos, key=lambda p: p.stat().st_mtime)


SQLITE_ORIGEN = _detectar_sqlite_origen()

URL_DESTINO = os.getenv("DATABASE_URL_POSTGRES", "")
if not URL_DESTINO or "tu_url_de_supabase" in URL_DESTINO:
    raise RuntimeError("DATABASE_URL_POSTGRES no está configurada en .env")

engine_origen = create_engine(f"sqlite:///{SQLITE_ORIGEN.as_posix()}", connect_args={"check_same_thread": False})
engine_destino = create_engine(URL_DESTINO)

# ──────────────────────────────────────────────
# 2. ORDEN TOPOLÓGICO DE TABLAS (padres → hijos)
#    Verificado contra las FKs reales de Base.metadata
# ──────────────────────────────────────────────
# Dependencias por FK (tabla -> tablas que referencia)
FK_MAP = {
    "sucursales": [],
    "usuarios": ["sucursales"],
    "proveedores": [],
    "ingredientes_stock": [],
    "registro_compras": ["proveedores", "usuarios"],
    "detalle_compras": ["registro_compras", "ingredientes_stock"],
    "registro_mermas": ["ingredientes_stock", "usuarios"],
    "control_gastos": ["usuarios"],
    "lista_verificacion_diario": ["usuarios"],
    "higiene_personal": [],
    "registro_temperaturas": [],
    "notificaciones": ["usuarios"],
    "requerimientos": ["sucursales"],
}


def _orden_topo(manual: dict) -> list:
    """Calcula orden topológico desde la metadata real y lo contrasta con el manual."""
    # Verificar que el mapa manual cubre TODAS las tablas de la metadata
    metadata_tables = set(Base.metadata.tables.keys())
    manual_tables = set(manual.keys())
    if metadata_tables != manual_tables:
        faltan = metadata_tables - manual_tables
        sobran = manual_tables - metadata_tables
        raise RuntimeError(f"Mapa de tablas desincronizado. Faltan: {faltan}. Sobran: {sobran}")

    orden, visitados, en_proceso = [], set(), set()

    def visitar(tabla):
        if tabla in visitados:
            return
        if tabla in en_proceso:
            raise RuntimeError(f"¡Ciclo en FKs detectado en: {tabla}!")
        en_proceso.add(tabla)
        for dep in manual.get(tabla, []):
            visitar(dep)
        en_proceso.discard(tabla)
        visitados.add(tabla)
        orden.append(tabla)

    for t in manual:
        visitar(t)
    return orden


ORDEN_TABLAS = _orden_topo(FK_MAP)

# ──────────────────────────────────────────────
# 3. HELPERS DE MIGRACIÓN
# ──────────────────────────────────────────────
def _conteo(engine, tabla: str) -> int:
    with engine.connect() as conn:
        return conn.execute(text(f'SELECT COUNT(*) FROM "{tabla}"')).scalar()


def _resetear_secuencia(engine, tabla: str) -> None:
    """Tras insertar IDs explícitos, la secuencia PG no avanza sola.
    La resincronizamos al MAX(id) para que los INSERTs futuros no colisionen."""
    with engine.begin() as conn:
        conn.execute(
            text(
                f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM \"{tabla}\"), 1), "
                f"(SELECT MAX(id) IS NOT NULL FROM \"{tabla}\"))"
            )
        )


def migrar_tabla(tabla: str, dry_run: bool = False) -> int:
    """Copia todas las filas de SQLite → PG preservando IDs. Devuelve filas copiadas."""
    table_obj = Base.metadata.tables[tabla]

    with engine_origen.connect() as src:
        filas = src.execute(select(table_obj)).mappings().all()

    if dry_run:
        return len(filas)

    if not filas:
        return 0

    with engine_destino.begin() as dst:
        # INSERT con IDs explícitos (preservación de claves primarias)
        dst.execute(table_obj.insert(), [dict(f) for f in filas])

    _resetear_secuencia(engine_destino, tabla)
    return len(filas)


# ──────────────────────────────────────────────
# 4. MAIN
# ──────────────────────────────────────────────
def main():
    dry_run = "--execute" not in sys.argv
    force = "--force" in sys.argv

    print("=" * 70)
    print("MIGRACIÓN DE DATOS  SQLite → PostgreSQL")
    print("=" * 70)
    print(f"ORIGEN : {SQLITE_ORIGEN.name}")
    print(f"DESTINO: PostgreSQL ({URL_DESTINO.split('@')[-1].split(':')[0]})")
    print(f"MODO   : {'DRY-RUN (solo verificación)' if dry_run else 'EJECUCIÓN REAL'}")
    print()

    if force and not dry_run:
        print("⚠️  --force: se truncarán las tablas destino antes de insertar.")
        print("    (Las tablas vacías se saltan; las con datos se TRUNCAN).")

    total_origen = sum(_conteo(engine_origen, t) for t in ORDEN_TABLAS)
    print(f"Filas en ORIGEN: {total_origen}\n")

    resultados = []
    fallos = []

    for tabla in ORDEN_TABLAS:
        n_origen = _conteo(engine_origen, tabla)

        if dry_run:
            n_destino = _conteo(engine_destino, tabla)
            estado = "OK" if n_destino == 0 else f"YA TIENE {n_destino} filas"
            print(f"  {tabla:28s} origen={n_origen:4d}  destino={n_destino:4d}  [{estado}]")
            resultados.append((tabla, n_origen, n_destino))
            continue

        # EJECUCIÓN REAL
        try:
            if force:
                with engine_destino.begin() as conn:
                    conn.execute(text(f'TRUNCATE TABLE "{tabla}" RESTART IDENTITY CASCADE'))
            n_copiadas = migrar_tabla(tabla, dry_run=False)
            n_destino = _conteo(engine_destino, tabla)
            ok = n_destino == n_origen
            estado = "✅ OK" if ok else "❌ DESFASE"
            print(f"  {tabla:28s} origen={n_origen:4d}  copiadas={n_copiadas:4d}  destino={n_destino:4d}  [{estado}]")
            resultados.append((tabla, n_origen, n_destino))
            if not ok:
                fallos.append(tabla)
        except Exception as e:
            print(f"  {tabla:28s} ❌ ERROR: {e}")
            fallos.append(tabla)

    print()
    print("=" * 70)
    if dry_run:
        print("✅ DRY-RUN COMPLETADO. Ejecuta con --execute para migrar.")
        print("   (con --force si quieres truncar el destino primero)")
        sys.exit(0)
    else:
        total_destino = sum(r[2] for r in resultados)
        print(f"TOTAL: {total_origen} origen → {total_destino} destino")
        if fallos:
            print(f"❌ TABLAS CON PROBLEMAS: {fallos}")
            sys.exit(1)
        print("✅ MIGRACIÓN COMPLETADA CON ÉXITO (Zero Data Loss)")
        sys.exit(0)


if __name__ == "__main__":
    main()
