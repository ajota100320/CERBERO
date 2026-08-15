"""Router del Módulo A: Recursos Humanos y Control de Asistencia.

API REST (GastroFlow / ERP).

Endpoints:
  GET  /api/v1/rrhh/empleados       → Lista de empleados del tenant.
  POST /api/v1/rrhh/empleados       → Crea un empleado (multi-tenant jerárquico:
                                       empresa_id del JWT + sucursal_id del payload).
  PUT  /api/v1/rrhh/empleados/{id}  → Actualiza un empleado.
  DELETE /api/v1/rrhh/empleados/{id}→ Elimina (borrado lógico vía activo=False).
  GET  /api/v1/rrhh/sucursales      → Sucursales del tenant (para selects).
  GET  /api/v1/rrhh/turnos/{empleado_id} → Historial de turnos de un empleado.
  POST /api/v1/rrhh/marcar-asistencia   → Marca entrada o salida según el estado
                                          del turno abierto de HOY.

Multi-Tenant estricto: todo se filtra por empresa_id del JWT. Nunca se confía en
un tenant enviado por el cliente.
"""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.main import require_auth, require_encargado_or_admin
from app.database import (
    get_db,
    Empleado,
    TurnoAsistencia,
    Sucursal,
)

router = APIRouter(prefix="/api/v1/rrhh", tags=["RRHH y Asistencia"])


def _serialize_empleado(e: Empleado) -> dict:
    return {
        "id": e.id,
        "nombre": e.nombre,
        "cargo": e.cargo or "",
        "sucursal_id": e.sucursal_id,
        "sucursal": e.sucursal.nombre if e.sucursal else f"Sucursal #{e.sucursal_id}",
        "activo": e.activo if e.activo is not None else True,
    }


def _serialize_turno(t: TurnoAsistencia) -> dict:
    return {
        "id": t.id,
        "empleado_id": t.empleado_id,
        "fecha": t.fecha.isoformat() if t.fecha else None,
        "hora_entrada": t.hora_entrada.isoformat() if t.hora_entrada else None,
        "hora_salida": t.hora_salida.isoformat() if t.hora_salida else None,
        "abierto": t.abierto,
    }


def _get_empleado_owned(db: Session, empleado_id: int, empresa_id: int) -> Empleado:
    """Valida que el empleado pertenezca al tenant (aislamiento multi-tenant)."""
    emp = (
        db.query(Empleado)
        .filter(
            Empleado.id == empleado_id,
            Empleado.empresa_id == empresa_id,
        )
        .first()
    )
    if not emp:
        raise HTTPException(status_code=404, detail=f"Empleado {empleado_id} no encontrado en la empresa")
    return emp


# ══════════════════════════════════════════════════
# CRUD EMPLEADOS
# ══════════════════════════════════════════════════
@router.get("/empleados")
async def listar_empleados(
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    items = (
        db.query(Empleado)
        .filter(Empleado.empresa_id == current_user.empresa_id)
        .order_by(Empleado.nombre)
        .all()
    )
    return [_serialize_empleado(e) for e in items]


@router.post("/empleados", status_code=status.HTTP_201_CREATED)
async def crear_empleado(
    payload: dict,
    current_user=Depends(require_encargado_or_admin),
    db: Session = Depends(get_db),
):
    nombre = (payload.get("nombre") or "").strip()
    if not nombre:
        raise HTTPException(status_code=422, detail="El nombre del empleado es obligatorio")

    sucursal_id = payload.get("sucursal_id")
    if not sucursal_id:
        raise HTTPException(status_code=422, detail="Debes asignar una sucursal al empleado")

    # Validar que la sucursal exista dentro del tenant (aislamiento jerárquico).
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

    nuevo = Empleado(
        empresa_id=current_user.empresa_id,
        nombre=nombre,
        cargo=(payload.get("cargo") or "").strip() or None,
        sucursal_id=int(sucursal_id),
        activo=True,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return _serialize_empleado(nuevo)


@router.put("/empleados/{empleado_id}")
async def actualizar_empleado(
    empleado_id: int,
    payload: dict,
    current_user=Depends(require_encargado_or_admin),
    db: Session = Depends(get_db),
):
    emp = _get_empleado_owned(db, empleado_id, current_user.empresa_id)

    if "nombre" in payload and payload["nombre"]:
        emp.nombre = (payload["nombre"]).strip()
    if "cargo" in payload:
        emp.cargo = (payload["cargo"] or "").strip() or None
    if "sucursal_id" in payload and payload["sucursal_id"]:
        sucursal = (
            db.query(Sucursal)
            .filter(
                Sucursal.id == int(payload["sucursal_id"]),
                Sucursal.empresa_id == current_user.empresa_id,
            )
            .first()
        )
        if not sucursal:
            raise HTTPException(status_code=404, detail=f"Sucursal {payload['sucursal_id']} no encontrada en la empresa")
        emp.sucursal_id = int(payload["sucursal_id"])
    if "activo" in payload:
        emp.activo = bool(payload["activo"])

    db.commit()
    db.refresh(emp)
    return _serialize_empleado(emp)


@router.delete("/empleados/{empleado_id}", status_code=status.HTTP_200_OK)
async def eliminar_empleado(
    empleado_id: int,
    current_user=Depends(require_encargado_or_admin),
    db: Session = Depends(get_db),
):
    """Borrado lógico: pone activo=False (preserva historial de turnos)."""
    emp = _get_empleado_owned(db, empleado_id, current_user.empresa_id)
    emp.activo = False
    db.commit()
    return {"message": "Empleado desactivado", "id": empleado_id}


# ══════════════════════════════════════════════════
# SUCURSALES DEL TENANT (para selects multi-tenant)
# ══════════════════════════════════════════════════
@router.get("/sucursales")
async def listar_sucursales_tenant(
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    items = (
        db.query(Sucursal)
        .filter(Sucursal.empresa_id == current_user.empresa_id)
        .order_by(Sucursal.nombre)
        .all()
    )
    return [{"id": s.id, "nombre": s.nombre} for s in items]


# ══════════════════════════════════════════════════
# RELOJ DE CONTROL (ASISTENCIA)
# ══════════════════════════════════════════════════
@router.get("/turnos/{empleado_id}")
async def historial_turnos(
    empleado_id: int,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    # Validar que el empleado pertenezca al tenant antes de listar sus turnos.
    _get_empleado_owned(db, empleado_id, current_user.empresa_id)
    turnos = (
        db.query(TurnoAsistencia)
        .filter(TurnoAsistencia.empleado_id == empleado_id)
        .order_by(TurnoAsistencia.fecha.desc(), TurnoAsistencia.id.desc())
        .all()
    )
    return [_serialize_turno(t) for t in turnos]


@router.post("/marcar-asistencia", status_code=status.HTTP_200_OK)
async def marcar_asistencia(
    payload: dict,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Marca entrada o salida según el estado del turno abierto de HOY.

    - Si el empleado NO tiene turno abierto hoy → marca hora_entrada (abre turno).
    - Si tiene turno abierto hoy → marca hora_salida (cierra turno).
    """
    empleado_id = payload.get("empleado_id")
    if not empleado_id:
        raise HTTPException(status_code=422, detail="Debes enviar el empleado_id")

    # Aislamiento multi-tenant: el empleado debe pertenecer a la empresa.
    _get_empleado_owned(db, int(empleado_id), current_user.empresa_id)

    hoy = date.today()
    ahora = datetime.now()

    turno_abierto = (
        db.query(TurnoAsistencia)
        .filter(
            TurnoAsistencia.empleado_id == int(empleado_id),
            TurnoAsistencia.fecha == hoy,
            TurnoAsistencia.hora_salida.is_(None),
        )
        .first()
    )

    if turno_abierto:
        # Cerrar turno: marcar salida.
        turno_abierto.hora_salida = ahora
        db.commit()
        db.refresh(turno_abierto)
        return {
            "message": "Salida marcada correctamente",
            "tipo": "salida",
            "turno": _serialize_turno(turno_abierto),
        }

    # Abrir turno: marcar entrada (reutiliza el registro del día si ya existe entrada sin salida).
    turno = (
        db.query(TurnoAsistencia)
        .filter(
            TurnoAsistencia.empleado_id == int(empleado_id),
            TurnoAsistencia.fecha == hoy,
        )
        .first()
    )
    if turno and turno.hora_entrada and turno.hora_salida:
        # Ya cerró turno hoy; no se reabre automáticamente.
        raise HTTPException(
            status_code=409,
            detail="El empleado ya cerró su turno hoy. Solo puede volver a marcar mañana.",
        )

    if turno:
        turno.hora_entrada = ahora
    else:
        turno = TurnoAsistencia(
            empleado_id=int(empleado_id),
            fecha=hoy,
            hora_entrada=ahora,
            hora_salida=None,
        )
        db.add(turno)
    db.commit()
    db.refresh(turno)
    return {
        "message": "Entrada marcada correctamente",
        "tipo": "entrada",
        "turno": _serialize_turno(turno),
    }
