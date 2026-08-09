#!/usr/bin/env python3
"""
Script independiente para limpiar datos semilla.
Elimina todos los registros de las tablas transaccionales y resetea el stock de ingredientes.
NO se importa ni se ejecuta en app/main.py. Solo para uso manual.
"""
import os
import sys

# Aseguramos que el directorio del proyecto esté en el path para importar app.*
PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ_DIR)

from app.database import SessionLocal, engine
from app.database import (
    RegistroCompra,
    DetalleCompra,
    RegistroMerma,
    ControlGasto,
    IngredienteStock,
)

def main():
    db = SessionLocal()
    try:
        print("Iniciando limpieza de datos semilla...")
        # Eliminar DetalleCompra primero (porque depende de RegistroCompra)
        print("Eliminando DetalleCompra...")
        db.query(DetalleCompra).delete()
        # Eliminar RegistroCompra
        print("Eliminando RegistroCompra...")
        db.query(RegistroCompra).delete()
        # Eliminar RegistroMerma
        print("Eliminando RegistroMerma...")
        db.query(RegistroMerma).delete()
        # Eliminar ControlGasto
        print("Eliminando ControlGasto...")
        db.query(ControlGasto).delete()
        # Resetear stock_actual de IngredienteStock a 0
        print("Reseteando stock_actual de IngredienteStock a 0...")
        db.query(IngredienteStock).update({IngredienteStock.stock_actual: 0.0})
        db.commit()
        print("Limpieza completada exitosamente.")
    except Exception as e:
        db.rollback()
        print(f"Error durante la limpieza: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()