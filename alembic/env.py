"""Alembic environment — configurado para el ERP Gastronómico.
Soporta multi-motor: SQLite (development) y PostgreSQL (production) vía .env.
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# ──────────────────────────────────────────────
# Asegurar que la raíz del proyecto esté en sys.path
# para poder importar app.database (Base + modelos)
# ──────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Cargar .env para resolver el motor activo (SQLite/PostgreSQL)
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from app.database import Base  # noqa: E402
from app import database  # noqa: E402  (importa los modelos y registra metadatos)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ──────────────────────────────────────────────
# target_metadata: metadatos de NUESTROS modelos
# ──────────────────────────────────────────────
target_metadata = Base.metadata


def _resolve_alembic_url() -> str:
    """Resuelve la URL de BD para Alembic:
    1. Si alembic.ini define sqlalchemy.url, lo usa (temporal, dev).
    2. Si no, usa el mismo motor que la app (app.database.DATABASE_URL),
       que ya resuelve ENVIRONMENT desde .env.
    """
    ini_url = config.get_main_option("sqlalchemy.url")
    if ini_url and ini_url != "driver://user:pass@localhost/dbname":
        return ini_url
    return database.DATABASE_URL


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (genera SQL sin conexión)."""
    url = _resolve_alembic_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (conexión real a la BD)."""
    # Inyectar la URL resuelta en la sección de config antes de crear el engine
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _resolve_alembic_url()

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
