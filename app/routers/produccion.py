"""Router del Motor de Producción (BOM - Bill of Materials).

API REST (GastroFlow / ERP) — Misión 2.

Endpoints:
  GET  /api/v1/produccion/recetas     → Fichas técnicas de la empresa (Recetario).
  GET  /api/v1/produccion/historial   → Ejecuciones recientes (Producción Diaria).
  POST /api/v1/produccion/ejecutar    → Descarga atómica de stock + registro de costo.

Lógica Transaccional Estricta (Pre-Flight Check):
  FASE A (Validación): itera los DetalleReceta, calcula cantidad_necesaria *
    multiplicador y verifica el stock de la Sucursal (StockSucursal). Si CUALQUIER
    insumo no alcanza → HTTPException(400) SIN guardar nada.
  FASE B (Ejecución): solo si A pasa limpia, restar stock (por sucursal + global),
    sumar costos y registrar HistorialProduccion.
  Todo bajo UN SOLO db.commit() protegido con try/except → db.rollback().

Multi-Tenant Híbrido:
  - La Receta pertenece a la Empresa (empresa_id del JWT).
  - El descuento de stock ocurre estrictamente en la Sucursal: la sucursal SIEMPRE
    proviene del usuario autenticado cuando este tiene una asignada (Operador/
    Encargado); solo Admin/SuperAdmin pueden ejecutar para una sucursal arbitraria.
  - El stock de la sucursal vive en StockSucursal (IngredienteStock es GLOBAL y NO
    tiene sucursal_id — se descuenta en ambos para mantener consistente la vista).
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.main import require_auth
from app.database import (
    get_db,
    Receta,
    DetalleReceta,
    HistorialProduccion,
    IngredienteStock,
    StockSucursal,
    UnidadMedida,
)

router = APIRouter(prefix="/api/v1/produccion", tags=["Produccion"])


def _unidad_str(value) -> str:
    return value.value if isinstance(value, UnidadMedida) else str(value)


# ══════════════════════════════════════════════════
# POST: Crear Ficha Técnica (Receta + Detalles) — Motor de Creación (UI).
# Multi-tenant intacto: receta y detalles se crean con empresa_id del JWT, y
# cada insumo del detalle se valida como perteneciente al tenant.
# ══════════════════════════════════════════════════
@router.post("/recetas", status_code=status.HTTP_201_CREATED)
async def crear_receta(
    payload: dict,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    empresa_id = current_user.empresa_id

    nombre = (payload.get("nombre") or "").strip()
    if not nombre:
        raise HTTPException(status_code=422, detail="El nombre de la receta es obligatorio")
    rendimiento_base = float(payload.get("rendimiento_base") or 1.0)
    if rendimiento_base <= 0:
        raise HTTPException(status_code=422, detail="El rendimiento base debe ser mayor a 0")

    detalles_payload = payload.get("detalles") or []
    if not detalles_payload:
        raise HTTPException(status_code=422, detail="La receta debe tener al menos un insumo")

    # Validar insumos dentro del tenant ANTES de persistir.
    detalles_validos = []
    for d in detalles_payload:
        insumo_id = d.get("insumo_id")
        cantidad = float(d.get("cantidad_necesaria") or d.get("cantidad") or 0)
        if not insumo_id or cantidad <= 0:
            raise HTTPException(status_code=422, detail="Cada insumo requiere insumo_id y cantidad > 0")
        insumo = (
            db.query(IngredienteStock)
            .filter(
                IngredienteStock.id == int(insumo_id),
                IngredienteStock.empresa_id == empresa_id,
                IngredienteStock.activo == True,
            )
            .first()
        )
        if not insumo:
            raise HTTPException(status_code=404, detail=f"Insumo {insumo_id} no encontrado en la empresa")
        detalles_validos.append({"insumo_id": int(insumo_id), "cantidad": cantidad})

    try:
        receta = Receta(
            empresa_id=empresa_id,
            nombre=nombre,
            descripcion=payload.get("descripcion"),
            rendimiento_base=rendimiento_base,
        )
        db.add(receta)
        db.flush()  # asigna receta.id

        for dv in detalles_validos:
            db.add(DetalleReceta(
                empresa_id=empresa_id,
                receta_id=receta.id,
                insumo_id=dv["insumo_id"],
                cantidad_necesaria=dv["cantidad"],
            ))

        # Un solo commit: si algo falla, la transacción entera se revierte.
        db.commit()
        db.refresh(receta)
    except Exception as exc:  # pragma: no cover - rollback defensivo
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear la receta: {exc}") from exc

    # Cargar detalles para la respuesta.
    receta.detalles = (
        db.query(DetalleReceta)
        .filter(DetalleReceta.receta_id == receta.id)
        .all()
    )
    return _serialize_receta(receta)


def _serialize_receta(r: Receta) -> dict:
    detalles = []
    for d in r.detalles:
        ins = d.insumo
        detalles.append({
            "id": d.id,
            "insumo_id": d.insumo_id,
            "insumo": ins.nombre if ins else f"Insumo #{d.insumo_id}",
            "cantidad_necesaria": round(d.cantidad_necesaria, 4),
            "unidad": _unidad_str(ins.unidad_medida) if ins else "",
        })
    return {
        "id": r.id,
        "nombre": r.nombre,
        "descripcion": r.descripcion,
        "rendimiento_base": r.rendimiento_base,
        "detalles": detalles,
    }


def _get_receta_owned(db: Session, receta_id: int, empresa_id: int) -> Receta:
    """Valida que la receta pertenezca al tenant (aislamiento)."""
    receta = (
        db.query(Receta)
        .filter(Receta.id == receta_id, Receta.empresa_id == empresa_id)
        .first()
    )
    if not receta:
        raise HTTPException(status_code=404, detail=f"Receta {receta_id} no encontrada en la empresa")
    return receta


def _get_stock_sucursal(db: Session, empresa_id: int, insumo_id: int, sucursal_id: int):
    """Stock de la sucursal para un insumo (None si la sucursal no tiene ese insumo)."""
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
# GET: Fichas técnicas (Recetario) — lista las recetas con sus insumos.
# ══════════════════════════════════════════════════
@router.get("/recetas")
async def listar_recetas(
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    items = (
        db.query(Receta)
        .filter(Receta.empresa_id == current_user.empresa_id)
        .order_by(Receta.nombre)
        .all()
    )
    return [_serialize_receta(r) for r in items]


# ══════════════════════════════════════════════════
# GET: Historial de producción (Producción Diaria) — ejecuciones recientes.
# ══════════════════════════════════════════════════
@router.get("/historial")
async def listar_historial(
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
    limite: int = 50,
):
    items = (
        db.query(HistorialProduccion)
        .filter(HistorialProduccion.empresa_id == current_user.empresa_id)
        .order_by(HistorialProduccion.fecha.desc())
        .limit(limite)
        .all()
    )
    return [{
        "id": h.id,
        "receta_id": h.receta_id,
        "receta": h.receta.nombre if h.receta else f"Receta #{h.receta_id}",
        "sucursal_id": h.sucursal_id,
        "sucursal": h.sucursal.nombre if h.sucursal else f"Sucursal #{h.sucursal_id}",
        "cantidad_producida": h.cantidad_producida,
        "costo_total_calculado": round(h.costo_total_calculado, 2),
        "fecha": h.fecha.isoformat() if h.fecha else None,
        "usuario_id": h.usuario_id,
    } for h in items]


# ══════════════════════════════════════════════════
# POST: EJECUTAR PRODUCCIÓN — Pre-Flight Check (Fase A) + Descuento (Fase B).
# ══════════════════════════════════════════════════
@router.post("/ejecutar", status_code=status.HTTP_200_OK)
async def ejecutar_produccion(
    payload: dict,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    receta_id = payload.get("receta_id")
    multiplicador = float(payload.get("multiplicador") or payload.get("cantidad") or 0)
    sucursal_id = current_user.sucursal_id or payload.get("sucursal_id")

    if not receta_id:
        raise HTTPException(status_code=422, detail="Se requiere receta_id")
    if multiplicador <= 0:
        raise HTTPException(status_code=422, detail="La cantidad (multiplicador) debe ser mayor a 0")
    if not sucursal_id:
        raise HTTPException(
            status_code=400,
            detail="El usuario no tiene una sucursal asignada para ejecutar producción",
        )

    empresa_id = current_user.empresa_id

    # ── Cargar receta del tenant + sus detalles (aislamiento por relación). ──
    receta = _get_receta_owned(db, int(receta_id), empresa_id)
    detalles = (
        db.query(DetalleReceta)
        .filter(DetalleReceta.receta_id == receta.id)
        .all()
    )
    if not detalles:
        raise HTTPException(status_code=422, detail="La receta no tiene insumos definidos")

    # ══════════════════════════════════════════════
    # FASE A (VALIDACIÓN) — NO escribe nada.
    # ══════════════════════════════════════════════
    plan = []  # [(detalle, required, stock_actual)] para reutilizar en Fase B
    for det in detalles:
        insumo = (
            db.query(IngredienteStock)
            .filter(
                IngredienteStock.id == det.insumo_id,
                IngredienteStock.empresa_id == empresa_id,
                IngredienteStock.activo == True,
            )
            .first()
        )
        if not insumo:
            raise HTTPException(status_code=404, detail=f"Insumo {det.insumo_id} no encontrado en la empresa")

        required = det.cantidad_necesaria * multiplicador

        stock_suc = _get_stock_sucursal(db, empresa_id, det.insumo_id, sucursal_id)
        stock_sucursal = stock_suc.stock_actual if stock_suc else 0.0

        # Si CUALQUIER insumo no alcanza → 400 SIN guardar nada.
        if (stock_sucursal or 0.0) < required:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para el insumo ID: {det.insumo_id} "
                       f"({insumo.nombre}) — se requieren {required:.4f} {_unidad_str(insumo.unidad_medida)} "
                       f"y hay {stock_sucursal:.4f} en la sucursal",
            )

        plan.append({
            "detalle": det,
            "insumo": insumo,
            "required": required,
            "stock_suc": stock_suc,
        })

    # ══════════════════════════════════════════════
    # FASE B (EJECUCIÓN) — solo si A pasó limpia.
    # ══════════════════════════════════════════════
    costo_total = 0.0
    try:
        for p in plan:
            insumo = p["insumo"]
            required = p["required"]

            # Descuento POR SUCURSAL (StockSucursal) — el stock real de la cocina.
            p["stock_suc"].stock_actual = (p["stock_suc"].stock_actual or 0.0) - required

            # Descuento GLOBAL (IngredienteStock) para mantener la vista central.
            insumo.stock_actual = (insumo.stock_actual or 0.0) - required

            # Costo monetario: cantidad requerida * costo_unitario del insumo.
            costo_total += required * (insumo.costo_unitario or 0.0)

        cantidad_producida = receta.rendimiento_base * multiplicador

        db.add(HistorialProduccion(
            empresa_id=empresa_id,
            receta_id=receta.id,
            sucursal_id=sucursal_id,
            cantidad_producida=cantidad_producida,
            costo_total_calculado=round(costo_total, 2),
            fecha=datetime.utcnow(),
            usuario_id=current_user.id,
        ))

        # UN solo commit: si algo falla, la transacción entera se revierte.
        db.commit()
    except Exception as exc:  # pragma: no cover - rollback defensivo
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al ejecutar la producción: {exc}",
        ) from exc

    return {
        "message": "Producción ejecutada correctamente",
        "receta": receta.nombre,
        "receta_id": receta.id,
        "sucursal_id": sucursal_id,
        "multiplicador": multiplicador,
        "cantidad_producida": cantidad_producida,
        "costo_total_calculado": round(costo_total, 2),
        "insumos_descontados": len(plan),
    }
