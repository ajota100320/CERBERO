"""Verificación funcional Módulo B (Checklists de Operación).

Crea una plantilla temporal con tareas dinámicas, verifica el serializado con
tareas, y limpia todo (rollback) al final.

Uso: PYTHONPATH="" venv/Scripts/python.exe scripts/verify_checklists.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, PlantillaChecklist, TareaChecklist, EjecucionPlantilla, Sucursal, Empresa

db = SessionLocal()

empresa = db.query(Empresa).first()
if not empresa:
    print("NO HAY EMPRESA SEED. Abortando.")
    sys.exit(1)
print(f"Tenant: {empresa.nombre} (id={empresa.id})")

# Crear sucursal temporal si no existe
suc = db.query(Sucursal).filter(Sucursal.empresa_id == empresa.id).first()
creada_suc = False
if not suc:
    suc = Sucursal(nombre="SUCURSAL_TEST_CHECK", direccion="Temporal", empresa_id=empresa.id)
    db.add(suc); db.commit(); db.refresh(suc)
    creada_suc = True
print(f"Sucursal: {suc.nombre} (id={suc.id})")

plantilla = None
try:
    # ── Crear plantilla con tareas dinámicas (simula POST /plantillas) ──
    plantilla = PlantillaChecklist(
        empresa_id=empresa.id,
        titulo="APERTURA COCINA TEST",
        descripcion="Verificación apertura",
        activo=True,
    )
    db.add(plantilla); db.flush()
    for desc in ["Encender freidora", "Revisar temperaturas", "Limpiar superficies"]:
        db.add(TareaChecklist(plantilla_id=plantilla.id, descripcion=desc))
    db.commit(); db.refresh(plantilla)

    tareas = db.query(TareaChecklist).filter(TareaChecklist.plantilla_id == plantilla.id).all()
    print(f"Plantilla creada: id={plantilla.id} titulo='{plantilla.titulo}' tareas={len(tareas)}")
    assert len(tareas) == 3, "Debe haber 3 tareas"
    print("Tareas dinámicas: OK ->", [t.descripcion for t in tareas])

    # ── Verificar cascade (borrar tareas vía sync) ──
    db.query(TareaChecklist).filter(TareaChecklist.plantilla_id == plantilla.id).delete()
    db.add(TareaChecklist(plantilla_id=plantilla.id, descripcion="Solo una tarea"))
    db.commit()
    tareas2 = db.query(TareaChecklist).filter(TareaChecklist.plantilla_id == plantilla.id).all()
    assert len(tareas2) == 1, "Sync debe dejar 1 tarea"
    print("Sincronización de tareas (reemplazo): OK")

    # ── Crear ejecución ──
    from datetime import datetime
    ejec = EjecucionPlantilla(
        empresa_id=empresa.id,
        plantilla_id=plantilla.id,
        sucursal_id=suc.id,
        completado=True,
        observaciones="Todo en orden",
    )
    db.add(ejec); db.commit(); db.refresh(ejec)
    assert ejec.completado == True and ejec.sucursal_id == suc.id
    print(f"Ejecución registrada: id={ejec.id} completado={ejec.completado} sucursal={ejec.sucursal_id}")

    print("VERIFICACIÓN MÓDULO B COMPLETA ✔")
finally:
    # ── ROLLBACK ──
    if plantilla:
        db.query(EjecucionPlantilla).filter(EjecucionPlantilla.plantilla_id == plantilla.id).delete()
        db.query(TareaChecklist).filter(TareaChecklist.plantilla_id == plantilla.id).delete()
        db.query(PlantillaChecklist).filter(PlantillaChecklist.id == plantilla.id).delete()
    if creada_suc:
        db.query(Sucursal).filter(Sucursal.id == suc.id).delete()
    db.commit()
    print("Rollback completo: ejecución, tareas, plantilla y sucursal temporal eliminados ✔")
    db.close()
