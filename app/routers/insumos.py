from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.main import require_auth
from app.database import get_db, IngredienteStock, CategoriaInsumo, UnidadMedida

router = APIRouter(prefix="/api/v1/insumos", tags=["Insumos"])


def _serialize(ins: IngredienteStock) -> dict:
    """Mapea la entidad SQLAlchemy al shape que espera el frontend Materio."""
    categoria_nombre = ins.categoria_obj.nombre if ins.categoria_obj else "Sin categoría"
    return {
        "id": ins.id,
        "sku": f"INS-{ins.id:05d}",
        "productName": ins.nombre,
        "category": categoria_nombre,
        "categoryId": ins.categoria_id,
        "stock": ins.stock_actual,
        "unit": ins.unidad_medida.value if isinstance(ins.unidad_medida, UnidadMedida) else str(ins.unidad_medida),
        "status": "Óptimo" if ins.stock_actual > ins.stock_minimo else "Bajo",
    }


def _parse_categoria_id(value, db: Session, empresa_id: int):
    """Resuelve categoria_id (int) o nombre de categoría → id en la tabla multi-tenant.
    Devuelve None si no se encuentra. NUNCA confía en ids de otros tenants."""
    if not value:
        return None
    if isinstance(value, int):
        # Validar que la categoría pertenezca a esta empresa
        cat = db.query(CategoriaInsumo).filter(
            CategoriaInsumo.id == value,
            CategoriaInsumo.empresa_id == empresa_id
        ).first()
        return cat.id if cat else None
    # Coerce por nombre (dentro del tenant)
    cat = db.query(CategoriaInsumo).filter(
        CategoriaInsumo.nombre == str(value).strip(),
        CategoriaInsumo.empresa_id == empresa_id
    ).first()
    return cat.id if cat else None


def _parse_unidad(value) -> UnidadMedida:
    """Coerce el valor libre del frontend al enum UnidadMedida."""
    if isinstance(value, UnidadMedida):
        return value
    for member in UnidadMedida:
        if member.value == value or member.name == value:
            return member
    return UnidadMedida.UNIDAD


@router.get("/")
async def read_insumos(
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    # Filtro Multi-Tenant estricto: SOLO insumos de la empresa del token JWT
    items = (
        db.query(IngredienteStock)
        .filter(IngredienteStock.empresa_id == current_user.empresa_id)
        .order_by(IngredienteStock.nombre)
        .all()
    )
    return [_serialize(item) for item in items]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_insumo(
    insumo: dict,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    # Inyección del tenant desde el JWT: NUNCA confiar en el payload del cliente
    nuevo = IngredienteStock(
        empresa_id=current_user.empresa_id,
        nombre=(insumo.get("productName") or insumo.get("nombre") or "").strip(),
        categoria_id=_parse_categoria_id(
            insumo.get("categoryId") if insumo.get("categoryId") is not None else (insumo.get("category") or insumo.get("categoria")),
            db, current_user.empresa_id
        ),
        unidad_medida=_parse_unidad(insumo.get("unit") or insumo.get("unidad_medida")),
        stock_actual=float(insumo.get("stock") or 0.0),
        stock_minimo=0.0,
        costo_unitario=0.0,
        costo_promedio=0.0,
        activo=True,
    )
    if not nuevo.nombre:
        raise HTTPException(status_code=422, detail="El nombre del insumo es obligatorio")

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return _serialize(nuevo)
