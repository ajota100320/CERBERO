"""Módulo Multi-Tenant - Aislamiento invisible por empresa (tenant).

CAPAS DE DEFENSA (defensa en profundidad):
  1. Columna `empresa_id` (FK -> empresas.id) en todo modelo TenantMixin.
  2. Este módulo: ContextVar `tenant_context` + filtrado automático en TODAS
     las sentencias SELECT/UPDATE/DELETE/INSERT sin tocar una sola ruta.
  3. Row Level Security (RLS) en PostgreSQL (migración Alembic).

REGLAS DE FUNCIONAMIENTO:
  - `tenant_context` se setea por request HTTP (desde el JWT) en
    `get_current_user` (app/main.py) y se resetea al final de la petición.
  - Si `tenant_context` está vacío (None) -> NO se filtra.
    Esto permite: login (el usuario aún no está autenticado), migraciones
    Alembic, scripts CLI y el seed inicial. Nunca lanza excepción.
  - Los INSERT reciben `empresa_id` automáticamente vía evento
    `before_flush` (el usuario NUNCA lo envía desde el formulario).

ESTRATEGIA DE FILTRADO (3 eventos):
  - monkey‑patch `Query.count()`: aplica WHERE antes de from_self/envuelto.
  - evento `before_compile` sobre Query: SELECT normales (all, first, etc.).
  - evento `do_orm_execute` sobre Session: UPDATE y DELETE.
  - evento `before_flush` sobre Session: inyecta empresa_id en INSERT.
"""
from contextvars import ContextVar

from sqlalchemy import event
from sqlalchemy.orm import Session, Query

from app.database import Base

# ──────────────────────────────────────────────
# CONTEXTO DE TENANT (por request)
# ──────────────────────────────────────────────
tenant_context: ContextVar = ContextVar("tenant_context", default=None)
sucursal_context: ContextVar = ContextVar("sucursal_context", default=None)


def set_tenant(empresa_id: int | None) -> None:
    """Establece el tenant activo para el request actual."""
    tenant_context.set(empresa_id)


def reset_tenant() -> None:
    """Limpia el tenant activo (fin de request / middleware)."""
    tenant_context.set(None)



# ──────────────────────────────────────────────
# CONTEXTO DE SUCURSAL (por request)
# ──────────────────────────────────────────────
def set_sucursal(sucursal_id: int | None) -> None:
    """Establece el sucursal activo para el request actual."""
    sucursal_context.set(sucursal_id)

def reset_sucursal() -> None:
    """Limpia el sucursal activo (fin de request / middleware)."""
    sucursal_context.set(None)

def get_sucursal() -> int | None:
    """Devuelve el sucursal activo (None si no hay contexto)."""
    return sucursal_context.get()
def get_tenant() -> int | None:
    """Devuelve el tenant activo (None si no hay contexto)."""
    return tenant_context.get()


# ──────────────────────────────────────────────
# HELPERS INTERNOS
# ──────────────────────────────────────────────
def _clase_para_tabla(nombre_tabla: str):
    """Mapea nombre de tabla -> clase ORM registrada (None si no existe)."""
    for mapper in Base.registry.mappers:
        tabla_local = getattr(mapper, "local_table", None)
        if tabla_local is not None and tabla_local.name == nombre_tabla:
            return mapper.class_
    return None


def _es_tenant_aware(cls) -> bool:
    """True si la clase hereda TenantMixin (tiene columna empresa_id)."""
    return hasattr(cls, "empresa_id")


def _aplicar_tenant_a_query(query, tenant_id):
    """Añade el WHERE empresa_id al query via _where_criteria (API interna).

    Se usa _where_criteria en vez de query.where() porque first() y otros
    métodos añaden LIMIT antes de compilar, y SQLAlchemy rechaza filter()
    sobre una query con LIMIT ya aplicado. _where_criteria es la receta
    oficial de multi‑tenant para inyectar criterios en cualquier momento.
    """
    if getattr(query, "_tenant_filtered", False):
        return query
    for desc in query.column_descriptions:
        entidad = desc.get("entity")
        if entidad is None:
            continue
        cls = entidad if isinstance(entidad, type) else entidad.__class__
        if _es_tenant_aware(cls):
            query._where_criteria += (cls.empresa_id == tenant_id,)
            query._tenant_filtered = True
            return query
    return query


# ══════════════════════════════════════════════════
# MONKEY‑PATCH: Query.count() con tenant (pre‑from_self)
# ══════════════════════════════════════════════════
# `count()` internamente envuelve la query con from_self(). Si el WHERE
# se añade en el evento before_compile, va al nivel externo y no filtra.
# El monkey‑patch aplica el WHERE ANTES de que count() haga el from_self.
_original_count = Query.count


def _tenant_aware_count(self):
    tenant_id = tenant_context.get()
    if tenant_id is not None and not getattr(self, "_tenant_filtered", False):
        for desc in self.column_descriptions:
            entity = desc.get("entity")
            if entity and _es_tenant_aware(entity):
                self._where_criteria += (getattr(entity, "empresa_id") == tenant_id,)
                self._tenant_filtered = True
                break
    return _original_count(self)


Query.count = _tenant_aware_count


# ──────────────────────────────────────────────
# EVENTO 1: BEFORE_COMPILE (SELECT — Query API)
# ──────────────────────────────────────────────
@event.listens_for(Query, "before_compile", retval=True)
def _filtro_select_before_compile(query):
    """Inyecta WHERE empresa_id en todo SELECT de la Query API.

    Cubre all(), first(), one(), one_or_none(), scalar() (no count),
    incluidas queries con joins y filtros adicionales.
    """
    tenant_id = tenant_context.get()
    if tenant_id is None:
        return query
    return _aplicar_tenant_a_query(query, tenant_id)


# ──────────────────────────────────────────────
# EVENTO 2: DO_ORM_EXECUTE (UPDATE / DELETE)
# ──────────────────────────────────────────────
@event.listens_for(Session, "do_orm_execute")
def _filtro_update_delete_execute(execute_state):
    """Inyecta WHERE empresa_id en UPDATE y DELETE.

    No filtra SELECTs aquí porque before_compile ya los cubre
    (evita doble WHERE redundante pero inocuo).
    """
    tenant_id = tenant_context.get()
    if tenant_id is None:
        return

    if execute_state.is_update or execute_state.is_delete:
        stmt = execute_state.statement
        tabla = getattr(stmt, "table", None)
        if tabla is not None:
            cls = _clase_para_tabla(tabla.name)
            if cls is not None and _es_tenant_aware(cls):
                stmt = stmt.where(cls.empresa_id == tenant_id)
                execute_state.statement = stmt


# ──────────────────────────────────────────────
# EVENTO 3: BEFORE_FLUSH (INSERT — inyección automática)
# ──────────────────────────────────────────────
@event.listens_for(Session, "before_flush")
def _inyectar_tenant_en_inserts(session, flush_context, instances):
    """Asigna empresa_id automáticamente a objetos nuevos tenant‑aware.

    El usuario nunca envía empresa_id: lo inyecta el sistema desde el
    contexto activo. Si no hay contexto (None), no toca nada (el objeto
    debe traer empresa_id explícito, p. ej. seed o migraciones).
    """
    tenant_id = tenant_context.get()
    if tenant_id is None:
        return
    for obj in session.new:
        if _es_tenant_aware(obj.__class__) and getattr(obj, "empresa_id", None) is None:
            obj.empresa_id = tenant_id