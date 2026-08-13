"""Router CRUD de Unidades de Medida - API REST (GastroFlow / ERP).

Multi-Tenant estricto: GET filtra por empresa_id del JWT; POST/PUT inyectan
empresa_id desde el token. NUNCA se confía en un tenant enviado por el cliente.
El borrado es lógico (activo=False).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.main import require_auth
from app.database import get_db, UnidadMedidaTabla

router = APIRouter(prefix="/api/v1/unidades", tags=["Unidades de Medida"])


def _serialize(u: UnidadMedidaTabla) -> dict:
    """Mapea la entidad SQLAlchemy al shape que espera el frontend Materio."""
    return {
        "id": u.id,
        "nombre": u.nombre,
        "abreviatura": u.abreviatura,
        "activo": u.activo if u.activo is not None else True,
    }


def _get_owned(db: Session, unidad_id: int, empresa_id: int) -> UnidadMedidaTabla:
    """Obtiene una unidad garantizando que pertenezca al tenant del token."""
    u = (
        db.query(UnidadMedidaTabla)
        .filter(
            UnidadMedidaTabla.id == unidad_id,
            UnidadMedidaTabla.empresa_id == empresa_id,
            UnidadMedidaTabla.activo == True,
        )
        .first()
    )
    if not u:
        raise HTTPException(status_code=404, detail="Unidad de medida no encontrada")
    return u


@router.get("/")
async def read_unidades(
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    # Filtro Multi-Tenant estricto: SOLO unidades de la empresa del token JWT
    items = (
        db.query(UnidadMedidaTabla)
        .filter(
            UnidadMedidaTabla.empresa_id == current_user.empresa_id,
            UnidadMedidaTabla.activo == True,
        )
        .order_by(UnidadMedidaTabla.nombre)
        .all()
    )
    return [_serialize(item) for item in items]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_unidad(
    unidad: dict,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    # Inyección del tenant desde el JWT: NUNCA confiar en el payload del cliente
    nombre = (unidad.get("nombre") or "").strip()
    abreviatura = (unidad.get("abreviatura") or "").strip()
    if not nombre:
        raise HTTPException(status_code=422, detail="El nombre de la unidad es obligatorio")
    if not abreviatura:
        raise HTTPException(status_code=422, detail="La abreviatura de la unidad es obligatoria")

    # Evitar duplicados dentro del mismo tenant
    existe = (
        db.query(UnidadMedidaTabla)
        .filter(
            UnidadMedidaTabla.nombre == nombre,
            UnidadMedidaTabla.empresa_id == current_user.empresa_id,
            UnidadMedidaTabla.activo == True,
        )
        .first()
    )
    if existe:
        raise HTTPException(status_code=409, detail="Ya existe una unidad de medida con ese nombre")

    nuevo = UnidadMedidaTabla(
        empresa_id=current_user.empresa_id,
        nombre=nombre,
        abreviatura=abreviatura,
        activo=True,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return _serialize(nuevo)


@router.put("/{unidad_id}/")
async def update_unidad(
    unidad_id: int,
    unidad: dict,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    u = _get_owned(db, unidad_id, current_user.empresa_id)
    nombre = (unidad.get("nombre") or "").strip()
    abreviatura = (unidad.get("abreviatura") or "").strip()
    if not nombre:
        raise HTTPException(status_code=422, detail="El nombre de la unidad es obligatorio")
    if not abreviatura:
        raise HTTPException(status_code=422, detail="La abreviatura de la unidad es obligatoria")

    u.nombre = nombre
    u.abreviatura = abreviatura
    db.commit()
    db.refresh(u)
    return _serialize(u)


@router.delete("/{unidad_id}/")
async def delete_unidad(
    unidad_id: int,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    # Borrado lógico (activo=False)
    u = _get_owned(db, unidad_id, current_user.empresa_id)
    u.activo = False
    db.commit()
    return {"message": "Unidad de medida eliminada", "id": unidad_id}
