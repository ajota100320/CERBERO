"""Router del Centro de Mando — KPIs del Dashboard (Misión 3, Ofensiva 1).

Multi-Tenant jerárquico: todas las métricas se calculan filtrando estrictamente
por empresa_id del JWT. NUNCA se confía en un tenant enviado por el cliente.

Endpoints:
  GET /api/v1/dashboard/kpis → 4 métricas en vivo:
    - requerimientos_pendientes : count de solicitudes en espera.
    - stock_critico            : count de insumos con stock_actual <= 10.
    - costo_estimado_hoy       : suma monetaria de requerimientos pendientes.
    - (bonus) sucursales_solicitando : número de sucursales con pedidos abiertos.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from app.main import require_auth
from app.database import (
    get_db,
    Requerimiento,
    DetalleRequerimiento,
    IngredienteStock,
    Sucursal,
    EstadoRequerimiento,
)

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])

# Umbral de stock crítico (límite arbitrario por ahora, configurable luego).
STOCK_CRITICO_LIMITE = 10.0


@router.get("/kpis")
async def dashboard_kpis(
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    empresa_id = current_user.empresa_id

    # ── 1. Requerimientos pendientes (PENDIENTE o CONSOLIDADO) ──
    requerimientos_pendientes = (
        db.query(func.count(func.distinct(Requerimiento.id)))
        .filter(
            Requerimiento.empresa_id == empresa_id,
            Requerimiento.estado.in_([
                EstadoRequerimiento.PENDIENTE,
                EstadoRequerimiento.CONSOLIDADO,
            ]),
        )
        .scalar()
        or 0
    )

    # ── 2. Stock crítico: insumos con stock_actual <= límite ──
    stock_critico = (
        db.query(func.count(IngredienteStock.id))
        .filter(
            IngredienteStock.empresa_id == empresa_id,
            IngredienteStock.activo == True,
            IngredienteStock.stock_actual <= STOCK_CRITICO_LIMITE,
        )
        .scalar()
        or 0
    )

    # ── 3. Costo estimado hoy: suma monetaria de requerimientos pendientes.
    # Se valora cada detalle pendiente con el costo_promedio del insumo.
    costo_estimado_hoy = (
        db.query(func.coalesce(
            func.sum(DetalleRequerimiento.cantidad_solicitada * IngredienteStock.costo_promedio),
            0.0,
        ))
        .join(Requerimiento, Requerimiento.id == DetalleRequerimiento.requerimiento_id)
        .join(IngredienteStock, IngredienteStock.id == DetalleRequerimiento.insumo_id)
        .filter(
            Requerimiento.empresa_id == empresa_id,
            Requerimiento.estado.in_([
                EstadoRequerimiento.PENDIENTE,
                EstadoRequerimiento.CONSOLIDADO,
            ]),
        )
        .scalar()
        or 0.0
    )

    # ── 4. Sucursales que están solicitando (bonus) ──
    sucursales_solicitando = (
        db.query(func.count(func.distinct(Requerimiento.sucursal_id)))
        .filter(
            Requerimiento.empresa_id == empresa_id,
            Requerimiento.estado.in_([
                EstadoRequerimiento.PENDIENTE,
                EstadoRequerimiento.CONSOLIDADO,
            ]),
        )
        .scalar()
        or 0
    )

    return {
        "requerimientos_pendientes": requerimientos_pendientes,
        "stock_critico": stock_critico,
        "costo_estimado_hoy": round(float(costo_estimado_hoy), 2),
        "sucursales_solicitando": sucursales_solicitando,
    }
