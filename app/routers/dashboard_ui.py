"""Vista HTML (Jinja2 + Tailwind CDN) del dashboard de inventario.
Solo lectura; reutiliza el serializador del router de insumos sin modificarlo."""
import os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.main import get_current_user
from app.database import get_db, IngredienteStock
from app.routers.insumos import _serialize

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"))
router = APIRouter(tags=["Dashboard UI"])


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_inventario(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user is None:
        return RedirectResponse("/docs", status_code=303)
    rows = (
        db.query(IngredienteStock)
        .filter(IngredienteStock.empresa_id == user.empresa_id, IngredienteStock.activo == True)
        .order_by(IngredienteStock.nombre)
        .all()
    )
    items = []
    for r in rows:
        d = _serialize(r)
        d["stock_minimo"] = r.stock_minimo or 0
        d["valor"] = round((r.stock_actual or 0) * (getattr(r, "costo_promedio", 0) or 0), 2)
        items.append(d)
    bajos = [i for i in items if i["status"] == "Bajo"]
    por_categoria = {}
    for i in items:
        por_categoria[i["category"]] = por_categoria.get(i["category"], 0) + 1
    ctx = {
        "user": user,
        "items": items,
        "bajos": bajos,
        "total_insumos": len(items),
        "total_bajos": len(bajos),
        "valor_total": round(sum(i["valor"] for i in items), 2),
        "por_categoria": sorted(por_categoria.items()),
    }
    return templates.TemplateResponse(request=request, name="dashboard/inventario.html", context=ctx)
