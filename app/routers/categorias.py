from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.main import require_auth
from app.database import get_db, CategoriaInsumo

router = APIRouter(prefix="/api/v1/categorias", tags=["Categorias"])


def _serialize(cat: CategoriaInsumo) -> dict:
    """Mapea la entidad SQLAlchemy al shape que espera el frontend Materio."""
    return {
        "id": cat.id,
        "nombre": cat.nombre,
        "descripcion": cat.descripcion or "",
        "activo": cat.activo if cat.activo is not None else True,
    }


@router.get("/")
async def read_categorias(
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    # Filtro Multi-Tenant estricto: SOLO categorías de la empresa del token JWT
    items = (
        db.query(CategoriaInsumo)
        .filter(CategoriaInsumo.empresa_id == current_user.empresa_id)
        .order_by(CategoriaInsumo.nombre)
        .all()
    )
    return [_serialize(item) for item in items]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_categoria(
    categoria: dict,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    # Inyección del tenant desde el JWT: NUNCA confiar en el payload del cliente
    nombre = (categoria.get("nombre") or "").strip()
    if not nombre:
        raise HTTPException(status_code=422, detail="El nombre de la categoría es obligatorio")

    # Evitar duplicados dentro del mismo tenant
    existe = (
        db.query(CategoriaInsumo)
        .filter(
            CategoriaInsumo.nombre == nombre,
            CategoriaInsumo.empresa_id == current_user.empresa_id,
        )
        .first()
    )
    if existe:
        raise HTTPException(status_code=409, detail="Ya existe una categoría con ese nombre")

    nueva = CategoriaInsumo(
        empresa_id=current_user.empresa_id,
        nombre=nombre,
        descripcion=(categoria.get("descripcion") or "").strip() or None,
        activo=True,
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return _serialize(nueva)
