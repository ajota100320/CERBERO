"""Router CRUD de Proveedores - API REST (GastroFlow / ERP).

Multi-Tenant estricto: GET filtra por empresa_id del JWT; POST/PUT inyectan
empresa_id desde el token. NUNCA se confía en un tenant enviado por el cliente.
El borrado es lógico (activo=False) para no romper la FK con compras.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.main import require_auth
from app.database import get_db, Proveedor

router = APIRouter(prefix="/api/v1/proveedores", tags=["Proveedores"])


def _serialize(prov: Proveedor) -> dict:
    """Mapea la entidad SQLAlchemy al shape que espera el frontend Materio."""
    return {
        "id": prov.id,
        "nombre": prov.nombre,
        "contacto": prov.contacto or "",
        "telefono": prov.telefono or "",
        "email": prov.email or "",
        "activo": prov.activo if prov.activo is not None else True,
    }


def _get_owned(db: Session, proveedor_id: int, empresa_id: int) -> Proveedor:
    """Obtiene un proveedor garantizando que pertenezca al tenant del token."""
    prov = (
        db.query(Proveedor)
        .filter(
            Proveedor.id == proveedor_id,
            Proveedor.empresa_id == empresa_id,
            Proveedor.activo == True,
        )
        .first()
    )
    if not prov:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return prov


@router.get("/")
async def read_proveedores(
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    # Filtro Multi-Tenant estricto: SOLO proveedores de la empresa del token JWT
    items = (
        db.query(Proveedor)
        .filter(
            Proveedor.empresa_id == current_user.empresa_id,
            Proveedor.activo == True,
        )
        .order_by(Proveedor.nombre)
        .all()
    )
    return [_serialize(item) for item in items]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_proveedor(
    proveedor: dict,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    # Inyección del tenant desde el JWT: NUNCA confiar en el payload del cliente
    nombre = (proveedor.get("nombre") or "").strip()
    if not nombre:
        raise HTTPException(status_code=422, detail="El nombre del proveedor es obligatorio")

    # Evitar duplicados dentro del mismo tenant
    existe = (
        db.query(Proveedor)
        .filter(
            Proveedor.nombre == nombre,
            Proveedor.empresa_id == current_user.empresa_id,
            Proveedor.activo == True,
        )
        .first()
    )
    if existe:
        raise HTTPException(status_code=409, detail="Ya existe un proveedor con ese nombre")

    nuevo = Proveedor(
        empresa_id=current_user.empresa_id,
        nombre=nombre,
        contacto=(proveedor.get("contacto") or "").strip() or None,
        telefono=(proveedor.get("telefono") or "").strip() or None,
        email=(proveedor.get("email") or "").strip() or None,
        activo=True,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return _serialize(nuevo)


@router.put("/{proveedor_id}/")
async def update_proveedor(
    proveedor_id: int,
    proveedor: dict,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    prov = _get_owned(db, proveedor_id, current_user.empresa_id)
    nombre = (proveedor.get("nombre") or "").strip()
    if not nombre:
        raise HTTPException(status_code=422, detail="El nombre del proveedor es obligatorio")

    prov.nombre = nombre
    prov.contacto = (proveedor.get("contacto") or "").strip() or None
    prov.telefono = (proveedor.get("telefono") or "").strip() or None
    prov.email = (proveedor.get("email") or "").strip() or None
    db.commit()
    db.refresh(prov)
    return _serialize(prov)


@router.delete("/{proveedor_id}/")
async def delete_proveedor(
    proveedor_id: int,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    # Borrado lógico (activo=False) para preservar integridad referencial con compras
    prov = _get_owned(db, proveedor_id, current_user.empresa_id)
    prov.activo = False
    db.commit()
    return {"message": "Proveedor eliminado", "id": proveedor_id}
