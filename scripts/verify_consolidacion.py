"""Verificación MISIÓN 2 — Motor de Consolidación matemática (producción).

Crea datos de prueba aislados, ejecuta la MISMA lógica SQL del endpoint
GET /api/v1/requerimientos/consolidados, valida el desglose por sucursal,
y luego ELIMINA todos los datos de prueba (rollback limpio).

Anti-script integrado: si algo falla, borra los datos creados igualmente.
"""
import sys
from datetime import datetime

# Asegurar que la raíz del proyecto esté en sys.path (el script corre desde scripts/).
import os
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import sqlalchemy as sa
from app.database import (
    DATABASE_URL, SessionLocal, Base,
    Sucursal, IngredienteStock, Requerimiento, DetalleRequerimiento,
    EstadoRequerimiento, UnidadMedida,
)
# Cargar app.main primero: registra los routers en orden, evitando el
# import circular (los routers hacen `from app.main import require_auth`).
import app.main  # noqa: F401,E402
from app.routers.requerimientos import _unidad_str

EMPRESA_TEST = 10
SUF = "__TEST_CONSOL__"

db = SessionLocal()
created = {"sucursales": [], "insumos": [], "requerimientos": []}

def cleanup():
    """Anti-script: elimina TODO lo creado por este test."""
    if created["requerimientos"]:
        for rid in created["requerimientos"]:
            db.query(DetalleRequerimiento).filter(DetalleRequerimiento.requerimiento_id == rid).delete()
            db.query(Requerimiento).filter(Requerimiento.id == rid).delete()
    if created["insumos"]:
        db.query(IngredienteStock).filter(IngredienteStock.nombre.like(f"%{SUF}%")).delete()
    if created["sucursales"]:
        db.query(Sucursal).filter(Sucursal.nombre.like(f"%{SUF}%")).delete()
    db.commit()

def ok(msg):
    print(f"  ✔ {msg}")

try:
    print("=== SETUP datos de prueba ===")
    # 2 sucursales de prueba
    s1 = Sucursal(nombre=f"Lira {SUF}", empresa_id=EMPRESA_TEST)
    s2 = Sucursal(nombre=f"Vitacura {SUF}", empresa_id=EMPRESA_TEST)
    db.add_all([s1, s2]); db.flush()
    created["sucursales"] = [s1.id, s2.id]
    ok(f"sucursales creadas: Lira(id={s1.id}), Vitacura(id={s2.id})")

    # 2 insumos de prueba
    i1 = IngredienteStock(nombre=f"Tomate {SUF}", empresa_id=EMPRESA_TEST,
                          unidad_medida=UnidadMedida.KG, stock_actual=0, stock_minimo=0,
                          costo_unitario=0, costo_promedio=0, activo=True)
    i2 = IngredienteStock(nombre=f"Cebolla {SUF}", empresa_id=EMPRESA_TEST,
                          unidad_medida=UnidadMedida.KG, stock_actual=0, stock_minimo=0,
                          costo_unitario=0, costo_promedio=0, activo=True)
    db.add_all([i1, i2]); db.flush()
    created["insumos"] = [i1.id, i2.id]
    ok(f"insumos creados: Tomate(id={i1.id}), Cebolla(id={i2.id})")

    # Requerimientos PENDIENTE:
    #  Lira:    Tomate 5, Cebolla 2
    #  Vitacura:Tomate 3, Cebolla 4
    #  Esperado: Tomate total 8 [Lira 5, Vitacura 3] | Cebolla total 6 [Lira 2, Vitacura 4]
    r_lira = Requerimiento(empresa_id=EMPRESA_TEST, sucursal_id=s1.id,
                           estado=EstadoRequerimiento.PENDIENTE, usuario_id=35)
    db.add(r_lira); db.flush()
    db.add_all([
        DetalleRequerimiento(requerimiento_id=r_lira.id, insumo_id=i1.id, cantidad_solicitada=5),
        DetalleRequerimiento(requerimiento_id=r_lira.id, insumo_id=i2.id, cantidad_solicitada=2),
    ])
    r_vita = Requerimiento(empresa_id=EMPRESA_TEST, sucursal_id=s2.id,
                           estado=EstadoRequerimiento.PENDIENTE, usuario_id=35)
    db.add(r_vita); db.flush()
    db.add_all([
        DetalleRequerimiento(requerimiento_id=r_vita.id, insumo_id=i1.id, cantidad_solicitada=3),
        DetalleRequerimiento(requerimiento_id=r_vita.id, insumo_id=i2.id, cantidad_solicitada=4),
    ])
    created["requerimientos"] = [r_lira.id, r_vita.id]
    db.commit()
    ok(f"requerimientos PENDIENTE creados: Lira #{r_lira.id}, Vitacura #{r_vita.id}")

    print("=== LÓGICA DE CONSOLIDACIÓN (copia exacta del endpoint) ===")
    # Totales por insumo
    totales = (
        db.query(
            IngredienteStock.id.label("insumo_id"),
            IngredienteStock.nombre.label("insumo"),
            IngredienteStock.unidad_medida.label("unidad"),
            sa.func.sum(DetalleRequerimiento.cantidad_solicitada).label("total"),
        )
        .join(DetalleRequerimiento, DetalleRequerimiento.insumo_id == IngredienteStock.id)
        .join(Requerimiento, Requerimiento.id == DetalleRequerimiento.requerimiento_id)
        .filter(Requerimiento.empresa_id == EMPRESA_TEST,
                Requerimiento.estado == EstadoRequerimiento.PENDIENTE)
        .group_by(IngredienteStock.id, IngredienteStock.nombre, IngredienteStock.unidad_medida)
        .order_by(IngredienteStock.nombre)
        .all()
    )
    detalle_por_insumo = (
        db.query(
            DetalleRequerimiento.insumo_id.label("insumo_id"),
            Sucursal.nombre.label("sucursal"),
            sa.func.sum(DetalleRequerimiento.cantidad_solicitada).label("cant"),
        )
        .join(Requerimiento, Requerimiento.id == DetalleRequerimiento.requerimiento_id)
        .join(Sucursal, Sucursal.id == Requerimiento.sucursal_id)
        .filter(Requerimiento.empresa_id == EMPRESA_TEST,
                Requerimiento.estado == EstadoRequerimiento.PENDIENTE)
        .group_by(DetalleRequerimiento.insumo_id, Sucursal.nombre)
        .all()
    )
    desglose_map = {}
    for row in detalle_por_insumo:
        desglose_map.setdefault(row.insumo_id, []).append(
            {"sucursal": row.sucursal, "cant": round(row.cant, 2)}
        )
    resultado = [{
        "insumo_id": t.insumo_id, "insumo": t.insumo,
        "unidad": _unidad_str(t.unidad), "total": round(t.total, 2),
        "detalle": desglose_map.get(t.insumo_id, []),
    } for t in totales]

    print("  RESULTADO:")
    for r in resultado:
        print(f"    - {r['insumo'].replace(' '+SUF,'')}: total={r['total']}kg  detalle={r['detalle']}")

    # ── VALIDACIÓN MATEMÁTICA ──
    print("=== VALIDACIÓN ===")
    by_name = {r["insumo"].replace(" " + SUF, ""): r for r in resultado}
    assert "Tomate" in by_name, "Tomate no apareció en consolidación"
    assert "Cebolla" in by_name, "Cebolla no apareció en consolidación"
    to = by_name["Tomate"]; ce = by_name["Cebolla"]

    # Tomate: total 8 = Lira 5 + Vitacura 3
    assert to["total"] == 8.0, f"Tomate total esperado 8, got {to['total']}"
    dto = {d["sucursal"]: d["cant"] for d in to["detalle"]}
    lira_t = [k for k in dto if "Lira" in k][0]
    vita_t = [k for k in dto if "Vitacura" in k][0]
    assert dto[lira_t] == 5.0, f"Lira Tomate esperado 5, got {dto[lira_t]}"
    assert dto[vita_t] == 3.0, f"Vitacura Tomate esperado 3, got {dto[vita_t]}"

    # Cebolla: total 6 = Lira 2 + Vitacura 4
    assert ce["total"] == 6.0, f"Cebolla total esperado 6, got {ce['total']}"
    dce = {d["sucursal"]: d["cant"] for d in ce["detalle"]}
    lira_c = [k for k in dce if "Lira" in k][0]
    vita_c = [k for k in dce if "Vitacura" in k][0]
    assert dce[lira_c] == 2.0, f"Lira Cebolla esperado 2, got {dce[lira_c]}"
    assert dce[vita_c] == 4.0, f"Vitacura Cebolla esperado 4, got {dce[vita_c]}"

    # Verificar desglose anidado: cada fila tiene sub-array 'detalle'
    assert all("detalle" in r for r in resultado), "Falta sub-array 'detalle' en consolidados"
    assert all(len(r["detalle"]) == 2 for r in resultado), "Cada insumo debe tener 2 sucursales"

    print()
    print("  ✔✔ TODAS LAS VALIDACIONES PASARON")
    print("  Formato de salida (ADN del endpoint):")
    print('    [{insumo: "Tomate", total: 8, detalle: [{sucursal: "Lira", cant: 5}, {sucursal: "Vitacura", cant: 3}]}]')

except AssertionError as e:
    print(f"  ✘ FALLÓ VALIDACIÓN: {e}")
    sys.exit(1)
except Exception as e:
    print(f"  ✘ ERROR: {type(e).__name__}: {e}")
    sys.exit(1)
finally:
    print("=== LIMPIEZA (anti-script) ===")
    cleanup()
    db.close()
    print("  ✔ datos de prueba eliminados — BD restaurada a estado original")
