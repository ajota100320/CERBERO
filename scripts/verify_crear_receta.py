"""Verify POST /api/v1/produccion/recetas (Motor de Creación UI) contra prod.
Datos transitorios + limpieza en finally (Zero residue)."""
import sys
from fastapi.testclient import TestClient
from app.main import app, create_access_token
from app.database import SessionLocal, Empresa, Sucursal, Usuario, RolUsuario, IngredienteStock, StockSucursal, UnidadMedida, Receta, DetalleReceta

client = TestClient(app)
EMPRESA_ID = 10
PASS, FAIL = "[PASS]", "[FAIL]"
res = []
def ck(l, c, e=""):
    res.append(c); print(f"{PASS if c else FAIL} {l} {e}")

db = SessionLocal()
suf = "_createrec"
try:
    emp = db.query(Empresa).filter(Empresa.id == EMPRESA_ID).first(); assert emp
    usr = Usuario(empresa_id=EMPRESA_ID, nombre_completo=f"Admin{suf}", email=f"admin{suf}@cert.local",
                  password_hash="x", rol=RolUsuario.ADMINISTRADOR, activo=True, debe_cambiar_password=False)
    db.add(usr); db.commit(); db.refresh(usr)
    ins1 = IngredienteStock(empresa_id=EMPRESA_ID, nombre=f"Insumo A{suf}", unidad_medida=UnidadMedida.KG, stock_actual=50.0, stock_minimo=0, costo_unitario=10.0, costo_promedio=10.0, activo=True)
    ins2 = IngredienteStock(empresa_id=EMPRESA_ID, nombre=f"Insumo B{suf}", unidad_medida=UnidadMedida.UNIDAD, stock_actual=50.0, stock_minimo=0, costo_unitario=5.0, costo_promedio=5.0, activo=True)
    db.add_all([ins1, ins2]); db.commit(); db.refresh(ins1); db.refresh(ins2)

    token = create_access_token({"sub": str(usr.id), "email": usr.email, "rol": usr.rol.value, "empresa_id": EMPRESA_ID})
    headers = {"Cookie": f"access_token={token}"}

    # 1) Sin nombre -> 422
    r = client.post("/api/v1/produccion/recetas", json={"detalles": [{"insumo_id": ins1.id, "cantidad_necesaria": 1}]}, headers=headers)
    ck("sin nombre 422", r.status_code == 422, f"(got {r.status_code})")

    # 2) Creación válida -> 201 con detalles
    r = client.post("/api/v1/produccion/recetas", json={
        "nombre": f"Receta{suf}", "descripcion": "Cert", "rendimiento_base": 2.0,
        "detalles": [
            {"insumo_id": ins1.id, "cantidad_necesaria": 3.0},
            {"insumo_id": ins2.id, "cantidad_necesaria": 1.5},
        ]}, headers=headers)
    ck("crear receta 201", r.status_code == 201, f"(got {r.status_code}: {r.text[:200]})")
    if r.status_code == 201:
        b = r.json()
        rid = b.get("id")
        ck("nombre correcto", b.get("nombre") == f"Receta{suf}")
        ck("rendimiento_base 2.0", b.get("rendimiento_base") == 2.0)
        ck("2 detalles", len(b.get("detalles", [])) == 2)
        ck("persistida en BD", db.query(Receta).filter(Receta.id == rid).count() == 1)
        ck("2 DetalleReceta en BD", db.query(DetalleReceta).filter(DetalleReceta.receta_id == rid).count() == 2)
finally:
    try:
        db.query(DetalleReceta).filter(DetalleReceta.receta_id.in_(
            db.query(Receta.id).filter(Receta.nombre == f"Receta{suf}"))).delete(synchronize_session=False)
        db.query(Receta).filter(Receta.nombre == f"Receta{suf}").delete()
        db.query(IngredienteStock).filter(IngredienteStock.nombre.like(f"%{suf}")).delete()
        db.query(Usuario).filter(Usuario.email == f"admin{suf}@cert.local").delete()
        db.commit()
    except Exception as e:
        db.rollback(); print(f"[WARN] limpieza: {e}")
    finally:
        db.close()

passed = sum(res)
print(f"\n=== verify-crear-receta: {passed}/{len(res)} PASS ===")
sys.exit(0 if passed == len(res) else 1)
