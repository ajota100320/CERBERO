"""Verificación Misión 2 — Motor de Recepción y Distribución de Stock (Ofensiva 1).

Prueba el endpoint POST /api/v1/requerimientos/recibir contra prod (Supabase)
con datos TRANSIENTES y limpieza automática:

  - Crea 2 sucursales de prueba + 1 insumo + 1 admin de prueba (mismo tenant).
  - Crea 2 requerimientos PENDIENTE (sucursal A pide 5, sucursal B pide 3) del
    MISMO insumo.
  - Llama al endpoint real vía TestClient (auth con cookie JWT).
  - Verifica distribución matemática: StockSucursal de A += 5, B += 3, y el
    stock global (IngredienteStock) += 8.
  - Verifica que los requerimientos quedaron en estado RECIBIDO.
  - finally: borra por sufijo identificable y assert residual = 0.

Correr: PYTHONPATH= ./venv/Scripts/python.exe scripts/verify_recibir.py
"""
import sys
from fastapi.testclient import TestClient

from app.main import app
from app.database import (
    SessionLocal, Empresa, Sucursal, IngredienteStock, StockSucursal,
    Requerimiento, DetalleRequerimiento, EstadoRequerimiento, Usuario, RolUsuario,
)
from app.main import get_password_hash

SUF = "VERIF_RECIBIR"

# ── 1. Sesión y TestClient ──
db = SessionLocal()
client = TestClient(app)

empresa = db.query(Empresa).filter(Empresa.id == 10).first() or db.query(Empresa).first()
empresa_id = empresa.id
print(f"Tenant de prueba: empresa_id={empresa_id}")

# ── 2. Seed de datos transient ──
suc_a = Sucursal(empresa_id=empresa_id, nombre=f"Sucursal A {SUF}")
suc_b = Sucursal(empresa_id=empresa_id, nombre=f"Sucursal B {SUF}")
db.add_all([suc_a, suc_b])
db.flush()

insumo = IngredienteStock(
    empresa_id=empresa_id,
    nombre=f"Insumo {SUF}",
    categoria_id=None,
    stock_actual=100.0,
    stock_minimo=0.0,
    costo_promedio=500.0,
    costo_unitario=500.0,
    activo=True,
)
db.add(insumo)
db.flush()

admin = Usuario(
    empresa_id=empresa_id,
    nombre_completo=f"Admin Verif {SUF}",
    email=f"admin_{SUF.lower()}@test.cl",
    password_hash=get_password_hash("Test1234!"),
    rol=RolUsuario.ADMINISTRADOR,
    activo=True,
    debe_cambiar_password=False,
    sucursal_id=None,
)
db.add(admin)
db.flush()

req_a = Requerimiento(empresa_id=empresa_id, sucursal_id=suc_a.id, estado=EstadoRequerimiento.PENDIENTE, usuario_id=admin.id)
req_b = Requerimiento(empresa_id=empresa_id, sucursal_id=suc_b.id, estado=EstadoRequerimiento.PENDIENTE, usuario_id=admin.id)
db.add_all([req_a, req_b])
db.flush()
db.add_all([
    DetalleRequerimiento(requerimiento_id=req_a.id, insumo_id=insumo.id, cantidad_solicitada=5.0),
    DetalleRequerimiento(requerimiento_id=req_b.id, insumo_id=insumo.id, cantidad_solicitada=3.0),
])
db.commit()
_admin_id = admin.id
_suc_a_id = suc_a.id
_suc_b_id = suc_b.id
_insumo_id = insumo.id
print(f"Seed: insumo={_insumo_id} stock_inicial={insumo.stock_actual}, req A={req_a.id} (5), req B={req_b.id} (3)")

try:
    # ── 3. Login y llamada al endpoint real ──
    login = client.post("/login", data={
        "email": admin.email,
        "password": "Test1234!",
    })
    assert login.status_code == 200, f"Login falló: {login.status_code} {login.text}"
    # Cookie JWT es secure=True (prod HTTPS) → httpx en HTTP no la reenvía sola.
    cookie = login.cookies.get("access_token")
    assert cookie, "No se obtuvo la cookie access_token"
    print("Login OK (cookie JWT emitida)")

    resp = client.post("/api/v1/requerimientos/recibir", cookies={"access_token": cookie})
    print(f"POST /recibir -> {resp.status_code}")
    body = resp.json()
    assert resp.status_code == 200, f"Recibir falló: {body}"
    print("Respuesta:", body)

    # ── 4. Verificaciones de distribución matemática ──
    db.expire_all()
    stock_a = db.query(StockSucursal).filter_by(
        empresa_id=empresa_id, ingrediente_id=insumo.id, sucursal_id=suc_a.id).first()
    stock_b = db.query(StockSucursal).filter_by(
        empresa_id=empresa_id, ingrediente_id=insumo.id, sucursal_id=suc_b.id).first()
    assert stock_a and stock_a.stock_actual == 5.0, f"Sucursal A debería tener 5, tiene {stock_a.stock_actual if stock_a else None}"
    assert stock_b and stock_b.stock_actual == 3.0, f"Sucursal B debería tener 3, tiene {stock_b.stock_actual if stock_b else None}"
    print(f"✔ DISTRIBUCIÓN POR SUCURSAL: A={stock_a.stock_actual}, B={stock_b.stock_actual}")

    db.expire_all()
    insumo_actual = db.query(IngredienteStock).filter_by(id=insumo.id).first()
    assert abs(insumo_actual.stock_actual - 108.0) < 1e-6, f"Stock global debería ser 108, es {insumo_actual.stock_actual}"
    print(f"✔ STOCK GLOBAL: {insumo_actual.stock_actual} (100 + 8)")

    # ── 5. Estados RECIBIDO ──
    db.expire_all()
    ra = db.query(Requerimiento).filter_by(id=req_a.id).first()
    rb = db.query(Requerimiento).filter_by(id=req_b.id).first()
    assert ra.estado == EstadoRequerimiento.RECIBIDO, f"req A estado={ra.estado}"
    assert rb.estado == EstadoRequerimiento.RECIBIDO, f"req B estado={rb.estado}"
    print("✔ ESTADOS: A y B en RECIBIDO")

    print("\n✅ TODAS LAS VERIFICACIONES PASARON")

finally:
    # ── 6. Limpieza transaccional (por sufijo / IDs pre-almacenados) ──
    db.expire_all()
    db.query(DetalleRequerimiento).filter(DetalleRequerimiento.requerimiento_id.in_(
        db.query(Requerimiento.id).filter(Requerimiento.usuario_id == _admin_id))).delete(synchronize_session=False)
    db.query(Requerimiento).filter(Requerimiento.usuario_id == _admin_id).delete(synchronize_session=False)
    db.query(StockSucursal).filter(StockSucursal.ingrediente_id == _insumo_id).delete(synchronize_session=False)
    db.query(IngredienteStock).filter(IngredienteStock.id == _insumo_id).delete(synchronize_session=False)
    db.query(Sucursal).filter(Sucursal.id.in_([_suc_a_id, _suc_b_id])).delete(synchronize_session=False)
    db.query(Usuario).filter(Usuario.id == _admin_id).delete(synchronize_session=False)
    db.commit()

    residual = (
        db.query(DetalleRequerimiento).filter(DetalleRequerimiento.requerimiento_id.in_(
            db.query(Requerimiento.id).filter(Requerimiento.usuario_id == _admin_id))).count()
        + db.query(Requerimiento).filter(Requerimiento.usuario_id == _admin_id).count()
        + db.query(IngredienteStock).filter(IngredienteStock.id == _insumo_id).count()
        + db.query(Sucursal).filter(Sucursal.id.in_([_suc_a_id, _suc_b_id])).count()
        + db.query(Usuario).filter(Usuario.id == _admin_id).count()
    )
    assert residual == 0, f"LIMIEZA INCOMPLETA, residual={residual}"
    print("🧹 Limpieza completada, residual = 0")
    db.close()
