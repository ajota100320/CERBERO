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

from app.main import require_auth
from app.database import (
    get_db,
    Requerimiento,
    DetalleRequerimiento,
    IngredienteStock,
    Sucursal,
    EstadoRequerimiento,
    UnidadMedida,
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
