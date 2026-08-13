import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal, Usuario, RolUsuario, init_db, Empresa
from app.main import get_password_hash
from datetime import datetime

def create_superuser():
    # Asegurar que las tablas existen
    init_db()
    db = SessionLocal()
    try:
        # 1. Buscar o Crear la Empresa Matriz (SaaS HQ)
        empresa = db.query(Empresa).filter(Empresa.nombre == "GastroFlow SaaS HQ").first()
        if not empresa:
            empresa = Empresa(
                nombre="GastroFlow SaaS HQ",
                rut="00.000.000-0",  # <--- EL FIX ESTÁ AQUÍ
                activa=True
            )
            db.add(empresa)
            db.flush() # Obliga a PostgreSQL a generar el ID
            print(f"✅ Empresa Matriz creada con ID: {empresa.id}")
        else:
            print(f"✅ Empresa Matriz encontrada con ID: {empresa.id}")

        # 2. Verificar si tu correo ya existe para actualizarlo
        email_admin = "ajota1003@gmail.com"
        existing = db.query(Usuario).filter(Usuario.email == email_admin).first()

        password = "123456"
        hashed_password = get_password_hash(password)

        if existing:
            # Si existe, lo actualizamos a la nueva arquitectura
            existing.empresa_id = empresa.id
            existing.rol = RolUsuario.SUPER_ADMIN
            existing.password_hash = hashed_password
            db.commit()
            print(f"✅ Superusuario actualizado con empresa_id {empresa.id} y rol SUPER_ADMIN")
        else:
            # 3. Si no existe, creamos el nuevo superusuario
            new_user = Usuario(
                nombre_completo="CEO GastroFlow",
                email=email_admin,
                password_hash=hashed_password,
                rol=RolUsuario.SUPER_ADMIN,
                empresa_id=empresa.id,
                activo=True
            )
            db.add(new_user)
            db.commit()
            print(f"✅ Superusuario creado exitosamente: {email_admin} (SUPER_ADMIN)")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_superuser()