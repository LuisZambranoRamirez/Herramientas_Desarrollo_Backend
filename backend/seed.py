"""
Script para inicializar usuarios de prueba en la base de datos.
Ejecución:
    python backend/seed.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from datetime import datetime, date
from app.database.connection import SessionLocal, engine, Base
from app.models.usuario import Usuario, UserRole
from app.models.paciente import Paciente
from app.core.security import get_password_hash

def seed():
    print("Conectando a la base de datos...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    now = datetime.utcnow()

    # 1. Crear Usuario Administrador (SYSTEM_ADMIN)
    admin_username = "admin"
    admin_password = "AdminPassword123!"

    user_admin = db.query(Usuario).filter(Usuario.username == admin_username).first()
    if not user_admin:
        user_admin = Usuario(
            username=admin_username,
            password=get_password_hash(admin_password),
            activo=True,
            user_role="SYSTEM_ADMIN",
            fecha_registro=now
        )
        db.add(user_admin)
        print(f"Usuario Administrador creado: {admin_username} / {admin_password}")
    else:
        print(f"El usuario '{admin_username}' ya existe.")

    # 2. Crear Usuario Paciente de prueba
    paciente_username = "paciente@correo.com"
    paciente_password = "password123"
    paciente_dni = "71234567"

    user_paciente = db.query(Usuario).filter(Usuario.username == paciente_username).first()
    if not user_paciente:
        user_paciente = Usuario(
            username=paciente_username,
            password=get_password_hash(paciente_password),
            activo=True,
            user_role="PACIENTE",
            fecha_registro=now
        )
        db.add(user_paciente)

        paciente_info = Paciente(
            dni=paciente_dni,
            username=paciente_username,
            nombres="Juan Carlos",
            apellidos="Pérez García",
            telefono="987654321",
            correo=paciente_username,
            direccion="Av. Principal 123",
            observaciones="Paciente de prueba inicial",
            fecha_nacimiento=date(1995, 5, 20),
            fecha_registro=now
        )
        db.add(paciente_info)
        print(f"Usuario Paciente creado: {paciente_username} / {paciente_password} (DNI: {paciente_dni})")
    else:
        print(f"El usuario '{paciente_username}' ya existe.")

    db.commit()
    db.close()
    print("Proceso de inicializacion finalizado exitosamente.")

if __name__ == "__main__":
    seed()
