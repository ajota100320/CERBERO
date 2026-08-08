import sys
sys.path.insert(0, 'C:/Users/hola/Documents/Mi segundo Cerebro/Nuevo proyecto ERP')

from app.database import SessionLocal, Usuario, RolUsuario, init_db
from app.main import get_password_hash

def create_superuser():
    # Asegurar que las tablas existen
    init_db()
    db = SessionLocal()
    try:
        # Verificar si ya existe
        existing = db.query(Usuario).filter(Usuario.email == 'ajota1003@gmail.com').first()
        if existing:
            # Actualizar password y rol por si acaso
            existing.password_hash = get_password_hash("123456")
            existing.rol = RolUsuario.ADMINISTRADOR
            existing.activo = True
            existing.nombre_completo = "Administrador Templo del Smash"
            db.commit()
            print("✅ Superusuario actualizado: ajota1003@gmail.com (ADMINISTRADOR)")
            return

        # Crear nuevo superusuario
        password = "123456"
        hashed_password = get_password_hash(password)
        new_user = Usuario(
            nombre_completo="Administrador Templo del Smash",
            email='ajota1003@gmail.com',
            password_hash=hashed_password,
            rol=RolUsuario.ADMINISTRADOR,
            activo=True
        )
        db.add(new_user)
        db.commit()
        print("✅ Superusuario creado exitosamente: ajota1003@gmail.com (ADMINISTRADOR)")
        print(f"   Hash bcrypt generado: {hashed_password[:20]}...")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_superuser()