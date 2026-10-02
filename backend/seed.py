"""
Script para inicializar usuarios y datos de prueba en la base de datos.
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
from app.models.personal import Personal
from app.models.odontologo import Odontologo, Especialidad
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

    # 3. Crear Odontólogos de prueba
    odontologos_data = [
        {
            "dni": "80123456",
            "username": "dr.mendoza",
            "password": "Doctor123!",
            "nombres": "Roberto",
            "apellidos": "Mendoza Salcedo",
            "telefono": "998877665",
            "correo": "dr.mendoza@solident.pe",
            "colegiatura": "COP-45892",
            "especialidad": "ORTODONCIA"
        },
        {
            "dni": "80654321",
            "username": "dra.paredes",
            "password": "Doctor123!",
            "nombres": "Claudia",
            "apellidos": "Paredes Vega",
            "telefono": "994433221",
            "correo": "dra.paredes@solident.pe",
            "colegiatura": "COP-51204",
            "especialidad": "ODONTOLOGIA_ESTETICA"
        }
    ]

    for od in odontologos_data:
        # Personal
        pers = db.query(Personal).filter(Personal.dni == od["dni"]).first()
        if not pers:
            pers = Personal(
                dni=od["dni"],
                nombres=od["nombres"],
                apellidos=od["apellidos"],
                telefono=od["telefono"],
                correo=od["correo"],
                activo=True,
                fecha_registro=now
            )
            db.add(pers)

        # Usuario
        usr = db.query(Usuario).filter(Usuario.username == od["username"]).first()
        if not usr:
            usr = Usuario(
                username=od["username"],
                password=get_password_hash(od["password"]),
                activo=True,
                user_role="ODONTOLOGO",
                fecha_registro=now
            )
            db.add(usr)

        # Odontólogo
        odont = db.query(Odontologo).filter(Odontologo.dni == od["dni"]).first()
        if not odont:
            odont = Odontologo(
                dni=od["dni"],
                colegiatura=od["colegiatura"],
                especialidad=od["especialidad"],
                username=od["username"]
            )
            db.add(odont)
            print(f"Odontólogo creado: Dr. {od['nombres']} {od['apellidos']} - {od['especialidad']} ({od['username']} / {od['password']})")

    db.commit()
    db.close()
    print("Proceso de inicialización finalizado exitosamente.")

if __name__ == "__main__":
    seed()
