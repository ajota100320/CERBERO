"""Certificación API Proveedores - TestClient autenticado contra prod (supabase).
Round-trip CRUD: GET(200) -> POST(201) -> GET(contiene) -> PUT(200) -> DELETE(200).
Teardown: hard-delete del registro de prueba para no ensuciar prod.
Uso: python scripts/verify-proveedores-api.py
"""
import sys, os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from app.main import app, create_access_token
from app.database import engine
from sqlalchemy import text

client = TestClient(app)

# Usuario real de prod (id=35, empresa_id=10) para el JWT
TOKEN = create_access_token(data={"sub": "35", "email": "ajota1003@gmail.com", "rol": "SuperAdmin", "empresa_id": 10})
client.cookies.set("access_token", TOKEN)

TEST_NOMBRE = "Proveedor Test Hermes __verif"
test_id = None
results = []

def check(label, cond, extra=""):
    results.append((label, bool(cond), extra))
    print(f"[{'PASS' if cond else 'FAIL'}] {label} {extra}")

# 1. GET lista -> 200 (certifica cero Error 500 por columnas faltantes)
r = client.get("/api/v1/proveedores/")
check("GET /api/v1/proveedores/ -> 200", r.status_code == 200, f"(status={r.status_code})")

# 2. POST crear -> 201
r = client.post("/api/v1/proveedores/", json={
    "nombre": TEST_NOMBRE, "contacto": "Juan Pérez", "telefono": "+56912345678", "email": "juan@test.cl"
})
check("POST crear -> 201", r.status_code == 201, f"(status={r.status_code})")
if r.status_code == 201:
    test_id = r.json()["id"]

# 3. GET verifica que aparece (multi-tenant)
r = client.get("/api/v1/proveedores/")
found = any(p["id"] == test_id for p in r.json())
check("GET contiene proveedor creado", r.status_code == 200 and found, f"(id={test_id})")

# 4. PUT actualizar -> 200
if test_id:
    r = client.put(f"/api/v1/proveedores/{test_id}/", json={
        "nombre": TEST_NOMBRE + " (edit)", "contacto": "Ana López", "telefono": "+56987654321", "email": "ana@test.cl"
    })
    check("PUT actualizar -> 200", r.status_code == 200 and r.json().get("contacto") == "Ana López", f"(status={r.status_code})")

# 5. DELETE -> 200 (soft delete)
if test_id:
    r = client.delete(f"/api/v1/proveedores/{test_id}/")
    check("DELETE -> 200", r.status_code == 200, f"(status={r.status_code})")

# 6. GET ya no lo lista (activo=False)
r = client.get("/api/v1/proveedores/")
gone = test_id is None or all(p["id"] != test_id for p in r.json())
check("GET ya no lista el eliminado", r.status_code == 200 and gone)

# TEARDOWN: hard-delete del registro de prueba (limpiar prod)
if test_id:
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM proveedores WHERE id = :i"), {"i": test_id})
        conn.commit()
    print(f"[TEARDOWN] Registro de prueba id={test_id} eliminado (hard)")

failed = [l for l, ok, _ in results if not ok]
print("\n=== RESUMEN ===")
print(f"{len(results) - len(failed)}/{len(results)} checks PASARON")
sys.exit(1 if failed else 0)
