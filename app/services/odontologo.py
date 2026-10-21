from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.models import Usuario
from app.models.models import Personal
from app.models.models import Odontologo, EspecialidadEnum
from app.core.security import get_password_hash
from app.schemas.odontologo import OdontologoCreate, OdontologoUpdate

def format_odontologo_response(o: Odontologo) -> dict:
    # Odontologo hereda de Personal (herencia por tablas unidas):
    # nombres, apellidos, telefono, correo, activo y fecha_registro viven en el mismo objeto.
    esp = o.especialidad.value if hasattr(o.especialidad, "value") else str(o.especialidad)

    return {
        "dni": o.dni,
        "username": o.username,
        "nombres": o.nombres,
        "apellidos": o.apellidos,
        "telefono": o.telefono,
        "correo": o.correo,
        "colegiatura": o.colegiatura,
        "especialidad": esp,
        "activo": o.activo,
        "fecha_registro": o.fecha_registro,
    }

def listar_especialidades() -> List[str]:
    return [e.value for e in EspecialidadEnum]

def listar_odontologos(
    db: Session,
    especialidad: Optional[str] = None,
    activo: Optional[bool] = None,
    query: Optional[str] = None
) -> List[dict]:
    # Odontologo ya incluye las columnas de Personal (JOIN automático por herencia)
    q = db.query(Odontologo)

    if especialidad:
        q = q.filter(Odontologo.especialidad == especialidad.upper())

    if activo is not None:
        q = q.filter(Odontologo.activo == activo)

    if query:
        search_filter = f"%{query.strip()}%"
        q = q.filter(
            or_(
                Odontologo.dni.ilike(search_filter),
                Odontologo.colegiatura.ilike(search_filter),
                Odontologo.nombres.ilike(search_filter),
                Odontologo.apellidos.ilike(search_filter)
            )
        )

    odontologos = q.order_by(Odontologo.apellidos.asc(), Odontologo.nombres.asc()).all()
    return [format_odontologo_response(o) for o in odontologos]

def obtener_perfil_odontologo(db: Session, current_user: Usuario) -> dict:
    odontologo = db.query(Odontologo).filter(Odontologo.username == current_user.username).first()
    if not odontologo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró un perfil de odontólogo asociado a tu cuenta"
        )
    return format_odontologo_response(odontologo)

def obtener_odontologo_por_dni(db: Session, dni: str) -> dict:
    odontologo = db.query(Odontologo).filter(Odontologo.dni == dni).first()
    if not odontologo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Odontólogo con DNI {dni} no encontrado"
        )
    return format_odontologo_response(odontologo)

def registrar_odontologo(db: Session, data: OdontologoCreate, current_user: Usuario) -> dict:
    if current_user.user_role != "SYSTEM_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden registrar nuevos odontólogos"
        )

    # Validaciones de unicidad
    if db.query(Personal).filter(Personal.dni == data.dni).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El DNI ya se encuentra registrado en el sistema"
        )

    if db.query(Usuario).filter(Usuario.username == data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El nombre de usuario '{data.username}' ya está en uso"
        )

    if db.query(Odontologo).filter(Odontologo.colegiatura == data.colegiatura).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de colegiatura ya está registrado"
        )

    if db.query(Personal).filter(Personal.correo == data.correo).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está en uso"
        )

    if db.query(Personal).filter(Personal.telefono == data.telefono).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de teléfono ya está en uso"
        )

    esp_upper = data.especialidad.upper()
    if esp_upper not in [e.value for e in EspecialidadEnum]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Especialidad no válida. Permitidas: {[e.value for e in EspecialidadEnum]}"
        )

    now = datetime.now(timezone.utc)

    # 1. Crear Usuario
    new_usuario = Usuario(
        username=data.username,
        password=get_password_hash(data.password),
        activo=True,
        user_role="ODONTOLOGO",
        fecha_registro=now
    )

    # 2. Crear Odontólogo. Por la herencia con Personal, SQLAlchemy inserta
    #    automáticamente la fila en `personal` y luego en `odontologo`.
    new_odontologo = Odontologo(
        dni=data.dni,
        nombres=data.nombres,
        apellidos=data.apellidos,
        telefono=data.telefono,
        correo=data.correo,
        activo=True,
        fecha_registro=now,
        colegiatura=data.colegiatura,
        especialidad=esp_upper,
        username=data.username
    )

    try:
        db.add(new_usuario)
        db.add(new_odontologo)
        db.commit()
        db.refresh(new_odontologo)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al registrar el odontólogo."
        )

    return format_odontologo_response(new_odontologo)

def actualizar_odontologo(db: Session, dni: str, data: OdontologoUpdate, current_user: Usuario) -> dict:
    odontologo = db.query(Odontologo).filter(Odontologo.dni == dni).first()
    if not odontologo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Odontólogo con DNI {dni} no encontrado"
        )

    if current_user.user_role != "SYSTEM_ADMIN" and odontologo.username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar los datos de este odontólogo"
        )

    personal = odontologo  # los datos personales viven en el mismo objeto (herencia)

    # Validar unicidad si cambia correo o teléfono
    if data.correo and data.correo != personal.correo:
        if db.query(Personal).filter(Personal.correo == data.correo, Personal.dni != dni).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado por otro personal"
            )
        personal.correo = data.correo

    if data.telefono and data.telefono != personal.telefono:
        if db.query(Personal).filter(Personal.telefono == data.telefono, Personal.dni != dni).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El teléfono ya está registrado por otro personal"
            )
        personal.telefono = data.telefono

    if data.colegiatura and data.colegiatura != odontologo.colegiatura:
        if db.query(Odontologo).filter(Odontologo.colegiatura == data.colegiatura, Odontologo.dni != dni).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El número de colegiatura ya está registrado"
            )
        odontologo.colegiatura = data.colegiatura

    if data.especialidad:
        esp_upper = data.especialidad.upper()
        if esp_upper not in [e.value for e in EspecialidadEnum]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Especialidad no válida. Permitidas: {[e.value for e in EspecialidadEnum]}"
            )
        odontologo.especialidad = esp_upper

    if data.nombres is not None:
        personal.nombres = data.nombres
    if data.apellidos is not None:
        personal.apellidos = data.apellidos
    if data.activo is not None and current_user.user_role == "SYSTEM_ADMIN":
        personal.activo = data.activo
        if odontologo.usuario:
            odontologo.usuario.activo = data.activo

    db.commit()
    db.refresh(odontologo)
    return format_odontologo_response(odontologo)

def cambiar_estado_odontologo(db: Session, dni: str, activo: bool, current_user: Usuario) -> dict:
    if current_user.user_role != "SYSTEM_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden cambiar el estado del odontólogo"
        )

    odontologo = db.query(Odontologo).filter(Odontologo.dni == dni).first()
    if not odontologo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Odontólogo con DNI {dni} no encontrado"
        )

    odontologo.activo = activo
    if odontologo.usuario:
        odontologo.usuario.activo = activo

    db.commit()
    estado_texto = "activado" if activo else "desactivado"
    return {"message": f"El odontólogo con DNI {dni} ha sido {estado_texto} exitosamente"}
