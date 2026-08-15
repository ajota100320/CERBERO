"""Router del Motor de Mermas (FASE 5 — Control de Fugas y Gastos).

API REST (GastroFlow / ERP) — Misión 1.

Endpoints:
  POST /api/v1/mermas/   → Registra una merma. Antes de guardar valida el stock
                           del insumo en la sucursal (StockSucursal). Si no
                           alcanza → 400 SIN tocar nada. Si hay stock, resta
                           (local + global), vincula el usuario_id del JWT y hace
                           UN SOLO db.commit().
  GET  /api/v1/mermas/   → Historial de mermas filtrado estrictamente por
                           empresa_id (tenant del JWT) y sucursal_id.

Reglas de Oro aplicadas:
  - FORENSE TRANSACCIONAL: try/except → db.rollback() → HTTPException(500).
  - MULTI-TENANT JERÁRQUICO: sucursal del usuario autenticado; empresa_id del JWT.
  - RED Y UX: 201 creación, 400 stock insuficiente, 404 insumo no encontrado,
              500 errores internos.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.main import require_auth
from app.database import (
    get_db,
    RegistroMerma,
    IngredienteStock,
    StockSucursal,
    TipoMerma,
    UnidadMedida,
)
from app.schemas import MermaCreate, MermaOut

router = APIRouter(prefix="/api/v1/mermas", tags=["Mermas"])


def _tipo_merma(value) -> TipoMerma:
    """Resuelve el enum TipoMerma desde un string con fallback seguro."""
    if isinstance(value, TipoMerma):
        return value
    if value:
        for t in TipoMerma:
            if t.value.lower() == str(value).lower():
                return t
    return TipoMerma.VENCIMIENTO


def _unidad_str(value) -> str:
    return value.value if isinstance(value, UnidadMedida) else str(value)


def _serialize(m: RegistroMerma) -> dict:
    ins = m.ingrediente
    return {
        "id": m.id,
        "insumo_id": m.ingrediente_id,
        "insumo": ins.nombre if ins else f"Insumo #{m.ingrediente_id}",
        "sucursal_id": m.sucursal_id,
        "sucursal": m.sucursal.nombre if m.sucursal else (f"Sucursal #{m.sucursal_id}" if m.sucursal_id else None),
        "cantidad": round(m.cantidad, 4),
        "motivo": m.observaciones,
        "costo_total": round(m.valor_perdida or 0.0, 2),
        "tipo": m.tipo.value if isinstance(m.tipo, TipoMerma) else str(m.tipo),
        "fecha_merma": m.fecha_merma.isoformat() if m.fecha_merma else None,
        "fecha_registro": m.fecha_registro.isoformat() if m.fecha_registro else None,
        "responsable_usuario_id": m.responsable_usuario_id,
        "estado": m.estado.value if hasattr(m.estado, "value") else str(m.estado),
    }


def _get_stock_sucursal(db: Session, empresa_id: int, insumo_id: int, sucursal_id: int):
    """Stock de la sucursal para un insumo (None si la sucursal no lo tiene)."""
    return (
        db.query(StockSucursal)
        .filter(
            StockSucursal.empresa_id == empresa_id,
            StockSucursal.ingrediente_id == insumo_id,
            StockSucursal.sucursal_id == sucursal_id,
        )
        .first()
    )


# ══════════════════════════════════════════════════
# POST: Registrar una merma.
# ══════════════════════════════════════════════════
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MermaOut)
async def registrar_merma(
    payload: MermaCreate,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    empresa_id = current_user.empresa_id

    # ── Sucursal: jerarquía multi-tenant. La del usuario manda; si es admin sin
    #    sucursal asignada, se acepta la enviada en el payload. ──
    sucursal_id = current_user.sucursal_id or payload.sucursal_id
    if not sucursal_id:
        raise HTTPException(
            status_code=400,
            detail="El usuario no tiene una sucursal asignada para registrar la merma",
        )

    # ── Validar que el insumo pertenezca al tenant (aislamiento). ──
    insumo = (
        db.query(IngredienteStock)
        .filter(
            IngredienteStock.id == payload.insumo_id,
            IngredienteStock.empresa_id == empresa_id,
            IngredienteStock.activo == True,
        )
        .first()
    )
    if not insumo:
        raise HTTPException(
            status_code=404,
            detail=f"Insumo {payload.insumo_id} no encontrado en la empresa",
        )

    # ══════════════════════════════════════════════
    # FASE A (VALIDACIÓN) — NO escribe nada.
    # ══════════════════════════════════════════════
    stock_suc = _get_stock_sucursal(db, empresa_id, payload.insumo_id, sucursal_id)
    stock_sucursal = stock_suc.stock_actual if stock_suc else 0.0

    # Si el stock de la sucursal es MENOR a la cantidad a mermar → 400 SIN guardar.
    if (stock_sucursal or 0.0) < payload.cantidad:
        raise HTTPException(
            status_code=400,
            detail="Stock insuficiente para registrar esta merma.",
        )

    # Costo: si no se envió, se calcula como cantidad × costo_promedio.
    costo_total = payload.costo_total
    if costo_total is None:
        costo_total = payload.cantidad * (insumo.costo_promedio or 0.0)

    # ══════════════════════════════════════════════
    # FASE B (EJECUCIÓN) — solo si A pasó limpia.
    # ══════════════════════════════════════════════
    try:
        # Descuento POR SUCURSAL (StockSucursal) — el stock real de la cocina.
        stock_suc.stock_actual = (stock_suc.stock_actual or 0.0) - payload.cantidad

        # Descuento GLOBAL (IngredienteStock) para mantener la vista central.
        insumo.stock_actual = (insumo.stock_actual or 0.0) - payload.cantidad

        nueva = RegistroMerma(
            ingrediente_id=payload.insumo_id,
            sucursal_id=sucursal_id,
            tipo=_tipo_merma(payload.tipo),
            cantidad=payload.cantidad,
            valor_perdida=round(costo_total, 2),
            fecha_merma=date.today(),
            observaciones=payload.motivo,
            responsable_usuario_id=current_user.id,
        )

        # UN solo commit: si algo falla, la transacción entera se revierte.
        db.add(nueva)
        db.commit()
        db.refresh(nueva)
    except Exception as exc:  # pragma: no cover - rollback defensivo
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar la merma: {exc}",
        ) from exc

    return _serialize(nueva)


# ══════════════════════════════════════════════════
# GET: Historial de mermas filtrado por empresa + sucursal.
# ══════════════════════════════════════════════════
@router.get("/", response_model=list[MermaOut])
async def listar_mermas(
    sucursal_id: int = Query(None, description="Filtro por sucursal. Default: la del usuario."),
    fecha_desde: date = Query(None, description="Filtro opcional por fecha (desde)."),
    fecha_hasta: date = Query(None, description="Filtro opcional por fecha (hasta)."),
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    empresa_id = current_user.empresa_id
    sucursal_filtro = sucursal_id or current_user.sucursal_id

    q = db.query(RegistroMerma).filter(
        RegistroMerma.empresa_id == empresa_id,
    )
    # Filtro obligatorio por sucursal (Regla 5): si el usuario tiene una, SIEMPRE
    # se aplica; un admin sin sucursal puede filtrar por cualquier sucursal_id.
    if sucursal_filtro:
        q = q.filter(RegistroMerma.sucursal_id == sucursal_filtro)

    if fecha_desde:
        q = q.filter(RegistroMerma.fecha_merma >= fecha_desde)
    if fecha_hasta:
        q = q.filter(RegistroMerma.fecha_merma <= fecha_hasta)

    items = q.order_by(RegistroMerma.fecha_registro.desc()).all()
    return [_serialize(m) for m in items]
