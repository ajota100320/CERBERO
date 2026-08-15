"""Router del Módulo B: Checklists de Operación.

API REST (GastroFlow / ERP).

Endpoints:
  GET  /api/v1/checklists/plantillas        → Plantillas del tenant (con tareas).
  POST /api/v1/checklists/plantillas        → Crea plantilla + tareas dinámicas.
  PUT  /api/v1/checklists/plantillas/{id}   → Actualiza plantilla y su lista de tareas.
  DELETE /api/v1/checklists/plantillas/{id} → Elimina (borrado lógico).
  GET  /api/v1/checklists/ejecuciones       → Ejecuciones del tenant.
  POST /api/v1/checklists/ejecuciones       → Registra una ejecución (completado).

Multi-Tenant estricto: todo se filtra por empresa_id del JWT. Nunca se confía en
un tenant enviado por el cliente. Las tareas (TareaChecklist) se acceden vía su
plantilla padre (aislamiento por relación).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.main import require_auth, require_encargado_or_admin
from app.database import (
    get_db,
    PlantillaChecklist,
    TareaChecklist,
    EjecucionPlantilla,
    Sucursal,
)

router = APIRouter(prefix="/api/v1/checklists", tags=["Checklists de Operación"])


def _serialize_tarea(t: TareaChecklist) -> dict:
    return {
        "id": t.id,
        "plantilla_id": t.plantilla_id,
        "descripcion": t.descripcion,
    }


def _serialize_plantilla(p: PlantillaChecklist) -> dict:
    return {
        "id": p.id,
        "titulo": p.titulo,
        "descripcion": p.descripcion or "",
        "activo": p.activo if p.activo is not None else True,
        "tareas": [_serialize_tarea(t) for t in p.tareas],
    }


def _serialize_ejecucion(e: EjecucionPlantilla) -> dict:
    return {
        "id": e.id,
        "plantilla_id": e.plantilla_id,
        "plantilla": e.plantilla.titulo if e.plantilla else f"Plantilla #{e.plantilla_id}",
        "sucursal_id": e.sucursal_id,
        "sucursal": e.sucursal.nombre if e.sucursal else f"Sucursal #{e.sucursal_id}",
        "fecha_ejecucion": e.fecha_ejecucion.isoformat() if e.fecha_ejecucion else None,
        "completado": e.completado,
        "observaciones": e.observaciones or "",
    }


def _get_plantilla_owned(db: Session, plantilla_id: int, empresa_id: int) -> PlantillaChecklist:
    """Valida que la plantilla pertenezca al tenant (aislamiento multi-tenant)."""
    p = (
        db.query(PlantillaChecklist)
        .filter(
            PlantillaChecklist.id == plantilla_id,
            PlantillaChecklist.empresa_id == empresa_id,
        )
        .first()
    )
    if not p:
        raise HTTPException(status_code=404, detail=f"Plantilla {plantilla_id} no encontrada en la empresa")
    return p


def _sync_tareas(db: Session, plantilla_id: int, tareas_payload: list):
    """Reemplaza la lista de tareas de una plantilla (cascade delete-orphan)."""
    # Borrar tareas existentes
    db.query(TareaChecklist).filter(TareaChecklist.plantilla_id == plantilla_id).delete()
    # Insertar nuevas (en orden)
    for desc in tareas_payload:
        txt = (desc or "").strip()
        if txt:
            db.add(TareaChecklist(plantilla_id=plantilla_id, descripcion=txt))


# ══════════════════════════════════════════════════
# CRUD PLANTILLAS
# ══════════════════════════════════════════════════
@router.get("/plantillas")
async def listar_plantillas(
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    items = (
        db.query(PlantillaChecklist)
        .filter(
            PlantillaChecklist.empresa_id == current_user.empresa_id,
            PlantillaChecklist.activo == True,
        )
        .order_by(PlantillaChecklist.titulo)
        .all()
    )
    return [_serialize_plantilla(p) for p in items]


@router.post("/plantillas", status_code=status.HTTP_201_CREATED)
async def crear_plantilla(
    payload: dict,
    current_user=Depends(require_encargado_or_admin),
    db: Session = Depends(get_db),
):
    titulo = (payload.get("titulo") or "").strip()
    if not titulo:
        raise HTTPException(status_code=422, detail="El título de la plantilla es obligatorio")

    nueva = PlantillaChecklist(
        empresa_id=current_user.empresa_id,
        titulo=titulo,
        descripcion=(payload.get("descripcion") or "").strip() or None,
        activo=True,
    )
    db.add(nueva)
    db.flush()  # asigna nueva.id

    _sync_tareas(db, nueva.id, payload.get("tareas") or [])
    db.commit()
    db.refresh(nueva)
    nueva.tareas = (
        db.query(TareaChecklist).filter(TareaChecklist.plantilla_id == nueva.id).all()
    )
    return _serialize_plantilla(nueva)


@router.put("/plantillas/{plantilla_id}")
async def actualizar_plantilla(
    plantilla_id: int,
    payload: dict,
    current_user=Depends(require_encargado_or_admin),
    db: Session = Depends(get_db),
):
    p = _get_plantilla_owned(db, plantilla_id, current_user.empresa_id)

    if "titulo" in payload and payload["titulo"]:
        p.titulo = (payload["titulo"]).strip()
    if "descripcion" in payload:
        p.descripcion = (payload["descripcion"] or "").strip() or None
    if "activo" in payload:
        p.activo = bool(payload["activo"])

    if "tareas" in payload:
        _sync_tareas(db, plantilla_id, payload["tareas"])

    db.commit()
    db.refresh(p)
    p.tareas = (
        db.query(TareaChecklist).filter(TareaChecklist.plantilla_id == plantilla_id).all()
    )
    return _serialize_plantilla(p)


@router.delete("/plantillas/{plantilla_id}", status_code=status.HTTP_200_OK)
async def eliminar_plantilla(
    plantilla_id: int,
    current_user=Depends(require_encargado_or_admin),
    db: Session = Depends(get_db),
):
    """Borrado lógico (activo=False); preserva ejecuciones históricas."""
    p = _get_plantilla_owned(db, plantilla_id, current_user.empresa_id)
    p.activo = False
    db.commit()
    return {"message": "Plantilla desactivada", "id": plantilla_id}


# ══════════════════════════════════════════════════
# EJECUCIONES DE CHECKLIST
# ══════════════════════════════════════════════════
@router.get("/ejecuciones")
async def listar_ejecuciones(
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    items = (
        db.query(EjecucionPlantilla)
        .filter(EjecucionPlantilla.empresa_id == current_user.empresa_id)
        .order_by(EjecucionPlantilla.fecha_ejecucion.desc())
        .all()
    )
    return [_serialize_ejecucion(e) for e in items]


@router.post("/ejecuciones", status_code=status.HTTP_201_CREATED)
async def crear_ejecucion(
    payload: dict,
    current_user=Depends(require_encargado_or_admin),
    db: Session = Depends(get_db),
):
    plantilla_id = payload.get("plantilla_id")
    sucursal_id = payload.get("sucursal_id")
    if not plantilla_id:
        raise HTTPException(status_code=422, detail="Debes enviar el plantilla_id")
    if not sucursal_id:
        raise HTTPException(status_code=422, detail="Debes enviar el sucursal_id")

    # Validar plantilla del tenant.
    _get_plantilla_owned(db, int(plantilla_id), current_user.empresa_id)
    # Validar sucursal del tenant (aislamiento jerárquico).
    sucursal = (
        db.query(Sucursal)
        .filter(
            Sucursal.id == int(sucursal_id),
            Sucursal.empresa_id == current_user.empresa_id,
        )
        .first()
    )
    if not sucursal:
        raise HTTPException(status_code=404, detail=f"Sucursal {sucursal_id} no encontrada en la empresa")

    nueva = EjecucionPlantilla(
        empresa_id=current_user.empresa_id,
        plantilla_id=int(plantilla_id),
        sucursal_id=int(sucursal_id),
        completado=bool(payload.get("completado", False)),
        observaciones=(payload.get("observaciones") or "").strip() or None,
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return _serialize_ejecucion(nueva)
