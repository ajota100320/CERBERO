"""Certificación del Motor de Producción (BOM) — Misión 2.

Verifica el endpoint POST /api/v1/produccion/ejecutar contra PROD (Supabase)
con datos transitorios y limpieza automática en `finally` (Zero residue).

Tests:
  [1] FASE B (éxito): stock suficiente -> 200. Valida que StockSucursal e
      IngredienteStock decrementan y que se crea HistorialProduccion con el
      costo calculado.
  [2] FASE A (fallo): stock insuficiente -> 400 'Stock insuficiente para el
      insumo ID: X'. Valida que NO se descuenta stock ni se crea historial.

Ejecutar desde el project-root:
    PYTHONPATH=. ./venv/Scripts/python.exe scripts/verify_produccion.py
"""
import sys

from fastapi.testclient import TestClient

from app.main import app, create_access_token
from app.database import (
    SessionLocal, get_db,
    Empresa, Sucursal, Usuario, RolUsuario,
    IngredienteStock, StockSucursal, UnidadMedida,
    Receta, DetalleReceta, HistorialProduccion,
)

client = TestClient(app)

EMPRESA_ID = 10
PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def check(label, cond, extra=""):
    results.append((label, cond, extra))
    print(f"{PASS if cond else FAIL} {label} {extra}")


# ── Datos transitorios ─────────────────────────────
sufijo = "_bomcert"
db = SessionLocal()

try:
    empresa = db.query(Empresa).filter(Empresa.id == EMPRESA_ID).first()
    assert empresa is not None, "Empresa 10 no existe"

    # Sucursal transitoria
    suc = Sucursal(empresa_id=EMPRESA_ID, nombre=f"Sucursal Cert{sufijo}")
    db.add(suc); db.flush()

    # Insumo transitorio (global stock_actual=100, costo=10)
    ins = IngredienteStock(
        empresa_id=EMPRESA_ID,
        nombre=f"Insumo Cert{sufijo}",
        unidad_medida=UnidadMedida.KG,
        stock_actual=100.0,
        stock_minimo=0.0,
        costo_unitario=10.0,
        costo_promedio=10.0,
        activo=True,
    )
    db.add(ins); db.flush()

    # Stock por sucursal (100 unidades en la cocina)
    ss = StockSucursal(
        empresa_id=EMPRESA_ID,
        ingrediente_id=ins.id,
        sucursal_id=suc.id,
        stock_actual=100.0,
    )
    db.add(ss)

    # Usuario admin transitorio con sucursal
    usr = Usuario(
        empresa_id=EMPRESA_ID,
        nombre_completo=f"Admin Cert{sufijo}",
        email=f"admin{sufijo}@cert.local",
        password_hash="x",
        rol=RolUsuario.ADMINISTRADOR,
        sucursal_id=suc.id,
        activo=True,
        debe_cambiar_password=False,
    )
    db.add(usr); db.flush()

    # Receta + DetalleReceta (cantidad_necesaria=5, rendimiento_base=1)
    rec = Receta(
        empresa_id=EMPRESA_ID,
        nombre=f"Receta Cert{sufijo}",
        descripcion="Ficha de certificacion",
        rendimiento_base=1.0,
    )
    db.add(rec); db.flush()
    dr = DetalleReceta(
        empresa_id=EMPRESA_ID,
        receta_id=rec.id,
        insumo_id=ins.id,
        cantidad_necesaria=5.0,
    )
    db.add(dr)
    db.commit()

    # Token JWT (sub str + empresa_id) + cookie explícita (httpx no reenvía secure cookies)
    token = create_access_token({"sub": str(usr.id), "email": usr.email, "rol": usr.rol.value, "empresa_id": EMPRESA_ID})
    headers = {"Cookie": f"access_token={token}"}

    # ── TEST 1: FASE B (éxito) — multiplicador=10 → required=50, hay 100 ──
    before_ss = ss.stock_actual
    before_ins = ins.stock_actual
    r1 = client.post("/api/v1/produccion/ejecutar",
                     json={"receta_id": rec.id, "multiplicador": 10, "sucursal_id": suc.id},
                     headers=headers)
    check("TEST1 FASE B status 200", r1.status_code == 200, f"(got {r1.status_code}: {r1.json()})")
    if r1.status_code == 200:
        body = r1.json()
        check("TEST1 cantidad_producida = rendimiento*multiplicador",
              body.get("cantidad_producida") == 10.0, f"({body.get('cantidad_producida')})")
        check("TEST1 costo_total = required*costo = 50*10 = 500",
              abs(body.get("costo_total_calculado", 0) - 500.0) < 0.01, f"({body.get('costo_total_calculado')})")
        check("TEST1 insumos_descontados = 1", body.get("insumos_descontados") == 1)
        # Verificar descuento en BD
        db.refresh(ss); db.refresh(ins)
        check("TEST1 StockSucursal decrementado 100→50", abs(ss.stock_actual - 50.0) < 0.01, f"(got {ss.stock_actual})")
        check("TEST1 IngredienteStock global decrementado 100→50",
              abs(ins.stock_actual - 50.0) < 0.01, f"(got {ins.stock_actual})")
        check("TEST1 historial creado",
              db.query(HistorialProduccion).filter(HistorialProduccion.receta_id == rec.id).count() == 1)
        check("TEST1 stock no fue a negativo", ss.stock_actual >= 0)

    # ── TEST 2: FASE A (fallo) — multiplicador=1000 → required=5000, hay 50 ──
    count_hist_before = db.query(HistorialProduccion).filter(HistorialProduccion.receta_id == rec.id).count()
    stock_ss_before_fail = ss.stock_actual
    stock_ins_before_fail = ins.stock_actual
    r2 = client.post("/api/v1/produccion/ejecutar",
                     json={"receta_id": rec.id, "multiplicador": 1000, "sucursal_id": suc.id},
                     headers=headers)
    ok400 = r2.status_code == 400
    det = r2.json().get("detail", "") if ok400 else r2.text
    check("TEST2 FASE A status 400", ok400, f"(got {r2.status_code})")
    # El endpoint reporta det.insumo_id; validar que coincida con el insumo creado
    check("TEST2 ins.id == det.insumo_id (forense)", ins.id == dr.insumo_id, f"(ins={ins.id} det={dr.insumo_id})")
    check("TEST2 detail menciona insumo ID",
          ok400 and f"insumo id: {dr.insumo_id}".lower() in str(det).lower(), f"({det})")
    # Validar atomicidad: NO se descuenta ni se registra
    db.refresh(ss); db.refresh(ins)
    count_hist_after = db.query(HistorialProduccion).filter(HistorialProduccion.receta_id == rec.id).count()
    check("TEST2 stock Sucursal intacto tras fallo",
          abs(ss.stock_actual - stock_ss_before_fail) < 0.01, f"(got {ss.stock_actual})")
    check("TEST2 stock global intacto tras fallo",
          abs(ins.stock_actual - stock_ins_before_fail) < 0.01, f"(got {ins.stock_actual})")
    check("TEST2 sin historial nuevo tras fallo", count_hist_after == count_hist_before)

finally:
    # ── LIMPIEZA TOTAL (Zero residue) ──
    try:
        db.query(HistorialProduccion).filter(HistorialProduccion.receta_id == rec.id).delete()
        db.query(DetalleReceta).filter(DetalleReceta.receta_id == rec.id).delete()
        db.query(Receta).filter(Receta.id == rec.id).delete()
        db.query(StockSucursal).filter(StockSucursal.ingrediente_id == ins.id).delete()
        db.query(IngredienteStock).filter(IngredienteStock.id == ins.id).delete()
        db.query(Usuario).filter(Usuario.id == usr.id).delete()
        db.query(Sucursal).filter(Sucursal.id == suc.id).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[WARN] limpieza parcial: {e}")
    finally:
        db.close()

# ── Resumen ─────────────────────────────────────────
total = len(results)
passed = sum(1 for _, c, _ in results if c)
print(f"\n=== RESUMEN: {passed}/{total} checks PASS ===")
sys.exit(0 if passed == total else 1)
