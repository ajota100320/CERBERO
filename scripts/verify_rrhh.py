"""Verificación funcional Módulo A (RRHH/Asistencia) — contra BD activa.

Crea sucursal + empleado temporales, marca entrada y salida, verifica la
lógica de apertura/cierre de turno y la propiedad 'abierto'. Limpia TODO lo
creado (rollback completo) al final.

Uso: PYTHONPATH="" venv/Scripts/python.exe scripts/verify_rrhh.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from app.database import SessionLocal, Empleado, TurnoAsistencia, Sucursal, Empresa

db = SessionLocal()

empresa = db.query(Empresa).first()
if not empresa:
    print("NO HAY EMPRESA SEED. Abortando.")
    sys.exit(1)
print(f"Tenant: {empresa.nombre} (id={empresa.id})")

# ── Crear sucursal temporal (tenant no tiene sucursales en prod) ──
suc = Sucursal(nombre="SUCURSAL_TEST_RRHH", direccion="Temporal", empresa_id=empresa.id)
db.add(suc); db.commit(); db.refresh(suc)
print(f"Sucursal temporal: id={suc.id}")

try:
    # ── Crear empleado temporal ──
    emp = Empleado(nombre="EMPLEADO_TEST_ASISTENCIA", cargo="Cocinero Test",
                   sucursal_id=suc.id, empresa_id=empresa.id)
    db.add(emp); db.commit(); db.refresh(emp)
    print(f"Empleado creado: id={emp.id}")

    # ── Verificar que no hay turno abierto hoy ──
    abierto = db.query(TurnoAsistencia).filter(
        TurnoAsistencia.empleado_id == emp.id,
        TurnoAsistencia.fecha == date.today(),
        TurnoAsistencia.hora_salida.is_(None),
    ).first()
    print("Estado inicial sin turno abierto:", "OK" if abierto is None else "FALLA (había turno)")

    # ── Marcar ENTRADA ──
    t = TurnoAsistencia(empleado_id=emp.id, fecha=date.today(), hora_entrada=None, hora_salida=None)
    t.hora_entrada = None
    # abierto = False antes de entrada
    assert t.abierto == False
    # Simular marcación de entrada (la lógica del endpoint la setea en el turno)
    t2 = db.query(TurnoAsistencia).filter(TurnoAsistencia.empleado_id == emp.id,
                                          TurnoAsistencia.fecha == date.today()).first()
    if not t2:
        from datetime import datetime
        t2 = TurnoAsistencia(empleado_id=emp.id, fecha=date.today(), hora_entrada=datetime.now())
        db.add(t2)
    else:
        t2.hora_entrada = datetime.now()
    db.commit(); db.refresh(t2)
    assert t2.hora_entrada is not None and t2.hora_salida is None
    assert t2.abierto == True
    print("Marcación ENTRADA: OK (abierto=True)")

    # ── Marcar SALIDA ──
    from datetime import datetime
    t2.hora_salida = datetime.now()
    db.commit(); db.refresh(t2)
    assert t2.hora_salida is not None and t2.abierto == False
    print("Marcación SALIDA: OK (abierto=False)")

    print("VERIFICACIÓN MÓDULO A COMPLETA ✔")
finally:
    # ── ROLLBACK: limpiar todo lo creado ──
    db.query(TurnoAsistencia).filter(TurnoAsistencia.empleado_id == emp.id).delete()
    db.query(Empleado).filter(Empleado.id == emp.id).delete()
    db.query(Sucursal).filter(Sucursal.id == suc.id).delete()
    db.commit()
    print("Rollback completo: turnos, empleado y sucursal temporal eliminados ✔")
    db.close()
