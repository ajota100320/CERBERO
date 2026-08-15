"""Verificación end-to-end del Motor de Mermas (FASE 5).

Corre contra una SQLite TEMPORAL (nunca toca producción Postgres/Supabase).
Prueba la lógica real de la API vía TestClient + token JWT firmado:
  1. POST con stock insuficiente -> 400 "Stock insuficiente..."
  2. POST con stock suficiente -> 201, descuenta StockSucursal e IngredienteStock
  3. GET filtrado por empresa + sucursal -> devuelve la merma creada
"""
import os
import sys
import tempfile

# Asegurar que la raíz del proyecto esté en sys.path (el script vive en scripts/).
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── Forzar ENVIRONMENT=development ANTES de importar app.* (load_dotenv no pisa env existente) ──
_TMP = os.path.abspath(os.path.join(tempfile.gettempdir(), "_test_mermas_f5.db"))
for k in list(os.environ):
    if k.startswith("DATABASE_URL"):
        del os.environ[k]
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL_SQLITE"] = f"sqlite:///{_TMP}"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import (  # noqa: E402
    Base, engine, SessionLocal,
    Empresa, Sucursal, Usuario, IngredienteStock, StockSucursal,
    CategoriaInsumo, RolUsuario, UnidadMedida,
)
from app.main import app, get_password_hash  # noqa: E402

PASS = "TestClave123!"


def setup():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    emp = Empresa(nombre="Empresa Test", rut="76.123.456-7")
    db.add(emp)
    db.flush()
    emp_id = emp.id
    suc = Sucursal(nombre="Sucursal Central", empresa_id=emp_id)
    db.add(suc)
    db.flush()
    suc_id = suc.id
    cat = CategoriaInsumo(nombre="Carnes", empresa_id=emp_id)
    db.add(cat)
    db.flush()
    ins = IngredienteStock(
        nombre="Tomate", empresa_id=emp_id, categoria_id=cat.id,
        unidad_medida=UnidadMedida.KG, stock_actual=10.0, costo_promedio=2.0,
    )
    db.add(ins)
    db.flush()
    ins_id = ins.id
    db.add(StockSucursal(
        empresa_id=emp_id, ingrediente_id=ins_id, sucursal_id=suc_id, stock_actual=10.0,
    ))
    user = Usuario(
        empresa_id=emp_id, nombre_completo="Operador Test", email="op@test.cl",
        password_hash=get_password_hash(PASS), rol=RolUsuario.OPERADOR,
        sucursal_id=suc_id, activo=True, debe_cambiar_password=False,
    )
    db.add(user)
    db.commit()
    user_id = user.id
    db.close()
    return {"empresa_id": emp_id, "sucursal_id": suc_id, "insumo_id": ins_id,
            "user_id": user_id, "email": user.email}


def main():
    d = setup()
    client = TestClient(app, base_url="https://testserver")

    # Login -> obtiene cookie access_token
    r = client.post("/login", data={"email": d["email"], "password": PASS, "remember": "true"})
    assert r.status_code == 200, f"login fallo {r.status_code}: {r.text}"

    ins_id, suc_id = d["insumo_id"], d["sucursal_id"]

    # 1) Stock insuficiente (hay 10, pedimos 20) -> 400
    r = client.post("/api/v1/mermas/", json={
        "insumo_id": ins_id, "cantidad": 20.0, "motivo": "prueba exceso",
    })
    assert r.status_code == 400, f"esperaba 400, got {r.status_code}: {r.text}"
    assert "Stock insuficiente" in r.json().get("detail", ""), r.json()
    print("  [OK] 400 stock insuficiente ->", r.json()["detail"])

    # 2) Stock suficiente (3 de 10) -> 201
    r = client.post("/api/v1/mermas/", json={
        "insumo_id": ins_id, "cantidad": 3.0, "motivo": "rotura en bodega",
    })
    assert r.status_code == 201, f"esperaba 201, got {r.status_code}: {r.text}"
    body = r.json()
    assert body["costo_total"] == 6.0, f"costo calculado mal: {body['costo_total']}"  # 3 * 2.0
    assert body["sucursal_id"] == suc_id, body
    assert body["responsable_usuario_id"] == d["user_id"], body
    print("  [OK] 201 merma creada id", body["id"], "costo_total", body["costo_total"])

    # Stock descontado: StockSucursal e IngredienteStock -> 7
    db = SessionLocal()
    ss = db.query(StockSucursal).filter_by(ingrediente_id=ins_id, sucursal_id=suc_id).first()
    ing = db.query(IngredienteStock).filter_by(id=ins_id).first()
    assert abs(ss.stock_actual - 7.0) < 1e-6, f"stock sucursal={ss.stock_actual}"
    assert abs(ing.stock_actual - 7.0) < 1e-6, f"stock global={ing.stock_actual}"
    print("  [OK] stock descontado: StockSucursal", ss.stock_actual, "| global", ing.stock_actual)

    # 3) GET filtrado por sucursal -> 1 merma
    r = client.get(f"/api/v1/mermas/?sucursal_id={suc_id}")
    assert r.status_code == 200, f"GET fallo {r.status_code}: {r.text}"
    items = r.json()
    assert len(items) == 1, f"esperaba 1 merma, got {len(items)}"
    assert items[0]["motivo"] == "rotura en bodega", items
    print("  [OK] GET historial filtrado: 1 merma, motivo ->", items[0]["motivo"])
    db.close()

    # Limpieza
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists(_TMP):
        os.remove(_TMP)
    print("\n✅ VERIFICACIÓN MERMAS F5 COMPLETA: 400 / 201 / descuento stock / GET filtrado — TODO OK")


if __name__ == "__main__":
    main()
