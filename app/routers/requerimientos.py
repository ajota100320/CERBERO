"""Router del Motor de Requerimientos Multi-Sucursal y Consolidación.

API REST (GastroFlow / ERP) — Misión 2.

Endpoints:
  POST /api/v1/requerimientos/           → Las cocinas envían su solicitud.
  GET  /api/v1/requerimientos/mis-solicitudes → Vista Cocina: SOLO la sucursal del
                                            usuario actual (current_user.sucursal_id).
  GET  /api/v1/requerimientos/consolidados   → Vista Administración: agrupa los
                                            detalles en estado 'PENDIENTE' de TODAS
                                            las sucursales de la empresa, devolviendo
                                            un desglose por sucursal.

Multi-Tenant estricto: todo se filtra por empresa_id del JWT. NUNCA se confía en un
tenant enviado por el cliente. DetalleRequerimiento se accede siempre vía su
Requerimiento padre (aislamiento por relación, no por columna).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from app.main import require_auth, require_admin
from app.database import (
    get_db,
    Requerimiento,
    DetalleRequerimiento,
    IngredienteStock,
    Sucursal,
    EstadoRequerimiento,
    UnidadMedida,
    StockSucursal,
)

router = APIRouter(prefix="/api/v1/requerimientos", tags=["Requerimientos"])


def _unidad_str(value) -> str:
    return value.value if isinstance(value, UnidadMedida) else str(value)


def _serialize_detalle(d: DetalleRequerimiento) -> dict:
    insumo_nombre = d.insumo.nombre if d.insumo else f"Insumo #{d.insumo_id}"
    unidad = _unidad_str(d.insumo.unidad_medida) if d.insumo else ""
    return {
        "id": d.id,
        "insumo_id": d.insumo_id,
        "insumo": insumo_nombre,
        "cantidad_solicitada": round(d.cantidad_solicitada, 2),
        "unidad": unidad,
    }


def _serialize(req: Requerimiento) -> dict:
    return {
        "id": req.id,
        "sucursal_id": req.sucursal_id,
        "sucursal": req.sucursal.nombre if req.sucursal else f"Sucursal #{req.sucursal_id}",
        "fecha_solicitud": req.fecha_solicitud.isoformat() if req.fecha_solicitud else None,
        "estado": req.estado.value if isinstance(req.estado, EstadoRequerimiento) else str(req.estado),
        "usuario_id": req.usuario_id,
        "detalles": [_serialize_detalle(d) for d in req.detalles],
    }


def _get_insumo_owned(db: Session, insumo_id: int, empresa_id: int) -> IngredienteStock:
    """Valida que el insumo pertenezca al tenant (aislamiento al crear detalle)."""
    ins = (
        db.query(IngredienteStock)
        .filter(
            IngredienteStock.id == insumo_id,
            IngredienteStock.empresa_id == empresa_id,
            IngredienteStock.activo == True,
        )
        .first()
    )
    if not ins:
        raise HTTPException(status_code=404, detail=f"Insumo {insumo_id} no encontrado en la empresa")
    return ins


# ══════════════════════════════════════════════════
# POST: Las cocinas envían sus solicitudes.
# ══════════════════════════════════════════════════
@router.post("/", status_code=status.HTTP_201_CREATED)
async def crear_requerimiento(
    payload: dict,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    # La sucursal SIEMPRE viene del usuario autenticado (jerarquía multi-tenant).
    # Nunca se acepta una sucursal_id arbitraria del payload.
    sucursal_id = current_user.sucursal_id
    if not sucursal_id:
        raise HTTPException(
            status_code=400,
            detail="El usuario no tiene una sucursal asignada para crear requerimientos",
        )

    detalles_payload = payload.get("detalles") or []
    if not detalles_payload:
        raise HTTPException(status_code=422, detail="El requerimiento debe tener al menos un detalle")

    # Validar insumos dentro del tenant ANTES de persistir (transacción segura).
    detalles_validos = []
    for d in detalles_payload:
        insumo_id = d.get("insumo_id") or d.get("id")
        cantidad = float(d.get("cantidad_solicitada") or d.get("cantidad") or 0)
        if not insumo_id or cantidad <= 0:
            raise HTTPException(status_code=422, detail="Cada detalle requiere insumo_id y cantidad > 0")
        _get_insumo_owned(db, int(insumo_id), current_user.empresa_id)
        detalles_validos.append({"insumo_id": int(insumo_id), "cantidad": cantidad})

    nuevo = Requerimiento(
        empresa_id=current_user.empresa_id,
        sucursal_id=sucursal_id,
        estado=EstadoRequerimiento.PENDIENTE,
        usuario_id=current_user.id,
    )
    db.add(nuevo)
    db.flush()  # asigna nuevo.id

    for dv in detalles_validos:
        db.add(DetalleRequerimiento(
            requerimiento_id=nuevo.id,
            insumo_id=dv["insumo_id"],
            cantidad_solicitada=dv["cantidad"],
        ))

    db.commit()
    db.refresh(nuevo)
    # Cargar detalles con relaciones para la respuesta.
    nuevo.detalles = (
        db.query(DetalleRequerimiento)
        .filter(DetalleRequerimiento.requerimiento_id == nuevo.id)
        .all()
    )
    return _serialize(nuevo)


# ══════════════════════════════════════════════════
# GET: Vista Cocina — solo los requerimientos de la sucursal del usuario.
# ══════════════════════════════════════════════════
@router.get("/mis-solicitudes")
async def mis_solicitudes(
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    if not current_user.sucursal_id:
        return []  # Usuario sin sucursal (admin) no tiene vista cocina.

    items = (
        db.query(Requerimiento)
        .filter(
            Requerimiento.empresa_id == current_user.empresa_id,
            Requerimiento.sucursal_id == current_user.sucursal_id,
        )
        .order_by(Requerimiento.fecha_solicitud.desc())
        .all()
    )
    # Forzar carga de detalles dentro del tenant.
    return [_serialize(r) for r in items]


# ══════════════════════════════════════════════════
# GET: Vista Administración — Consolidación matemática de compras.
# Agrupa los detalles 'PENDIENTE' de TODAS las sucursales de la empresa.
# Devuelve: [{insumo, insumo_id, total, unidad, detalle:[{sucursal, cant}, ...]}]
# ══════════════════════════════════════════════════
@router.get("/consolidados")
async def consolidados(
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    empresa_id = current_user.empresa_id

    # 1. Total por insumo (todos los PENDIENTE de la empresa).
    totales = (
        db.query(
            IngredienteStock.id.label("insumo_id"),
            IngredienteStock.nombre.label("insumo"),
            IngredienteStock.unidad_medida.label("unidad"),
            func.sum(DetalleRequerimiento.cantidad_solicitada).label("total"),
        )
        .join(DetalleRequerimiento, DetalleRequerimiento.insumo_id == IngredienteStock.id)
        .join(Requerimiento, Requerimiento.id == DetalleRequerimiento.requerimiento_id)
        .filter(
            Requerimiento.empresa_id == empresa_id,
            Requerimiento.estado == EstadoRequerimiento.PENDIENTE,
        )
        .group_by(IngredienteStock.id, IngredienteStock.nombre, IngredienteStock.unidad_medida)
        .order_by(IngredienteStock.nombre)
        .all()
    )

    # 2. Desglose por sucursal para cada insumo (sub-array anidado).
    detalle_por_insumo = (
        db.query(
            DetalleRequerimiento.insumo_id.label("insumo_id"),
            Sucursal.nombre.label("sucursal"),
            func.sum(DetalleRequerimiento.cantidad_solicitada).label("cant"),
        )
        .join(Requerimiento, Requerimiento.id == DetalleRequerimiento.requerimiento_id)
        .join(Sucursal, Sucursal.id == Requerimiento.sucursal_id)
        .filter(
            Requerimiento.empresa_id == empresa_id,
            Requerimiento.estado == EstadoRequerimiento.PENDIENTE,
        )
        .group_by(DetalleRequerimiento.insumo_id, Sucursal.nombre)
        .order_by(Sucursal.nombre)
        .all()
    )

    # Construir mapa insumo_id → [desglose por sucursal]
    desglose_map = {}
    for row in detalle_por_insumo:
        desglose_map.setdefault(row.insumo_id, []).append({
            "sucursal": row.sucursal,
            "cant": round(row.cant, 2),
        })

    resultado = [
        {
            "insumo_id": t.insumo_id,
            "insumo": t.insumo,
            "unidad": _unidad_str(t.unidad),
            "total": round(t.total, 2),
            "detalle": desglose_map.get(t.insumo_id, []),
        }
        for t in totales
    ]

    return resultado


# ══════════════════════════════════════════════════
# POST: Cierre del ciclo de compras — Recepción y distribución de stock.
# Administración confirma que la compra global fue realizada. El endpoint:
#   1) Busca los requerimientos PENDIENTE / CONSOLIDADO de la empresa.
#   2) Itera sobre cada DetalleRequerimiento.
#   3) SUMA la cantidad comprada al stock del insumo en la sucursal que ORIGINÓ
#      el pedido (StockSucursal por sucursal_id + total global en IngredienteStock).
#      (Lira pidió 5 y Vitacura 3 → +5 a Lira, +3 a Vitacura.)
#   4) Cambia el estado de los requerimientos a 'RECIBIDO'.
# Todo dentro de UN SOLO bloque db.commit() para evitar datos huérfanos.
# ══════════════════════════════════════════════════
@router.post("/recibir", status_code=status.HTTP_200_OK)
async def recibir_compra_global(
    current_user=Depends(require_admin),  # Solo Administración / Super Admin
    db: Session = Depends(get_db),
):
    empresa_id = current_user.empresa_id

    # 1. Requerimientos pendientes de recibir (PENDIENTE o CONSOLIDADO) del tenant.
    requisitos = (
        db.query(Requerimiento)
        .filter(
            Requerimiento.empresa_id == empresa_id,
            Requerimiento.estado.in_([
                EstadoRequerimiento.PENDIENTE,
                EstadoRequerimiento.CONSOLIDADO,
            ]),
        )
        .all()
    )

    if not requisitos:
        raise HTTPException(
            status_code=404,
            detail="No hay requerimientos PENDIENTES o CONSOLIDADOS por recibir",
        )

    resumen_sucursales: dict[int, dict] = {}  # sucursal_id -> {nombre, cant_total}
    insumos_afectados = 0

    # 2. Iterar requerimientos → 3. distribuir stock → 4. cambiar estado.
    for req in requisitos:
        # Forzar carga de detalles dentro del tenant (aislamiento por relación).
        detalles = (
            db.query(DetalleRequerimiento)
            .filter(DetalleRequerimiento.requerimiento_id == req.id)
            .all()
        )
        for det in detalles:
            # ── Stock POR SUCURSAL (la que originó el pedido) ──
            stock_suc = (
                db.query(StockSucursal)
                .filter(
                    StockSucursal.empresa_id == empresa_id,
                    StockSucursal.ingrediente_id == det.insumo_id,
                    StockSucursal.sucursal_id == req.sucursal_id,
                )
                .first()
            )
            if not stock_suc:
                stock_suc = StockSucursal(
                    empresa_id=empresa_id,
                    ingrediente_id=det.insumo_id,
                    sucursal_id=req.sucursal_id,
                    stock_actual=0.0,
                )
                db.add(stock_suc)
            stock_suc.stock_actual = (stock_suc.stock_actual or 0.0) + det.cantidad_solicitada

            # ── Stock GLOBAL (IngredienteStock) para la vista central ──
            insumo = (
                db.query(IngredienteStock)
                .filter(
                    IngredienteStock.id == det.insumo_id,
                    IngredienteStock.empresa_id == empresa_id,
                )
                .first()
            )
            if insumo:
                insumo.stock_actual = (insumo.stock_actual or 0.0) + det.cantidad_solicitada

            insumos_afectados += 1

            # Resumen por sucursal (solo para la respuesta informativa).
            res = resumen_sucursales.setdefault(req.sucursal_id, {
                "sucursal_id": req.sucursal_id,
                "nombre": req.sucursal.nombre if req.sucursal else f"Sucursal #{req.sucursal_id}",
                "cantidad_total": 0.0,
            })
            res["cantidad_total"] += det.cantidad_solicitada

        # 4. Cambiar estado.
        req.estado = EstadoRequerimiento.RECIBIDO

    # UN solo commit: si algo falla arriba, la transacción entera se revierte.
    db.commit()

    return {
        "message": "Compra global recibida. Stock distribuido por sucursal.",
        "requerimientos_recibidos": len(requisitos),
        "insumos_afectados": insumos_afectados,
        "sucursales": list(resumen_sucursales.values()),
    }
