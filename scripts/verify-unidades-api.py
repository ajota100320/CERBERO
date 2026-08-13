"""Certificación API Unidades de Medida - TestClient autenticado contra prod (supabase).
Round-trip CRUD: GET(200) -> POST(201) -> GET(contiene) -> PUT(200) -> DELETE(200).
Teardown: hard-delete del registro de prueba para no ensuciar prod.
Uso: python scripts/verify-unidades-api.py
"""
import sys, os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from app.main import app, create_access_token
from app.database import engine
from sqlalchemy import text

client = TestClient(app)
TOKEN = create_access_token(data={"sub": "35", "email": "ajota1003@gmail.com", "rol": "SuperAdmin", "empresa_id": 10})
client.cookies.set("access_token", TOKEN)

TEST_NOMBRE = "Unidad Test Hermes __verif"
test_id = None
results = []

def check(label, cond, extra=""):
    results.append((label, bool(cond), extra))
    print(f"[{'PASS' if cond else 'FAIL'}] {label} {extra}")

# 1. GET lista -> 200 (certifica cero Error 500 por columnas faltantes)
r = client.get("/api/v1/unidades/")
check("GET /api/v1/unidades/ -> 200", r.status_code == 200, f"(status={r.status_code})")

# 2. POST crear -> 201
r = client.post("/api/v1/unidades/", json={"nombre": TEST_NOMBRE, "abreviatura": "UT"})
check("POST crear -> 201", r.status_code == 201, f"(status={r.status_code})")
if r.status_code == 201:
    test_id = r.json()["id"]

# 3. GET verifica que aparece (multi-tenant)
r = client.get("/api/v1/unidades/")
found = any(u["id"] == test_id for u in r.json())
check("GET contiene unidad creada", r.status_code == 200 and found, f"(id={test_id})")

# 4. PUT actualizar -> 200
if test_id:
    r = client.put(f"/api/v1/unidades/{test_id}/", json={"nombre": TEST_NOMBRE + " (edit)", "abreviatura": "UTE"})
    check("PUT actualizar -> 200", r.status_code == 200 and r.json().get("abreviatura") == "UTE", f"(status={r.status_code})")

# 5. DELETE -> 200 (soft delete)
if test_id:
    r = client.delete(f"/api/v1/unidades/{test_id}/")
    check("DELETE -> 200", r.status_code == 200, f"(status={r.status_code})")

# 6. GET ya no lo lista (activo=False)
r = client.get("/api/v1/unidades/")
gone = test_id is None or all(u["id"] != test_id for u in r.json())
check("GET ya no lista la eliminada", r.status_code == 200 and gone)

# TEARDOWN: hard-delete del registro de prueba (limpiar prod)
if test_id:
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM unidades_medida WHERE id = :i"), {"i": test_id})
        conn.commit()
    print(f"[TEARDOWN] Registro de prueba id={test_id} eliminado (hard)")

failed = [l for l, ok, _ in results if not ok]
print("\n=== RESUMEN ===")
print(f"{len(results) - len(failed)}/{len(results)} checks PASARON")
sys.exit(1 if failed else 0)
