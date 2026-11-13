import unicodedata
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.models import (
    Usuario,
    Personal,
    Odontologo,
    HorarioPersonal,
    DiaSemanaEnum,
    EspecialidadEnum,
    UserRoleEnum,
)
from app.core.security import get_password_hash
from app.schemas.odontologo import OdontologoCreate, OdontologoUpdate

def format_odontologo_response(o: Odontologo) -> dict:
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
    q = db.query(Odontologo)
    if especialidad:
        try:
            esp_enum = EspecialidadEnum(especialidad.strip().upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Especialidad no válida. Permitidas: {[e.value for e in EspecialidadEnum]}",
            )
        q = q.filter(Odontologo.especialidad == esp_enum)
    if activo is not None:
        q = q.filter(Odontologo.activo == activo)
    if query:
        search_filter = f"%{query.strip()}%"
        q = q.filter(
            or_(
                Odontologo.dni.ilike(search_filter),
                Odontologo.colegiatura.ilike(search_filter),
                Odontologo.nombres.ilike(search_filter),
                Odontologo.apellidos.ilike(search_filter),
            )
        )
    odontologos = q.order_by(Odontologo.apellidos.asc(), Odontologo.nombres.asc()).all()
    return [format_odontologo_response(o) for o in odontologos]

def obtener_perfil_odontologo(db: Session, current_user: Usuario) -> dict:
    odontologo = db.query(Odontologo).filter(Odontologo.username == current_user.username).first()
    if not odontologo:
        raise HTTPException(status_code=404, detail="No se encontró un perfil de odontólogo asociado a tu cuenta")
    return format_odontologo_response(odontologo)

def obtener_odontologo_por_dni(db: Session, dni: str) -> dict:
    odontologo = db.query(Odontologo).filter(Odontologo.dni == dni).first()
    if not odontologo:
        raise HTTPException(status_code=404, detail=f"Odontólogo con DNI {dni} no encontrado")
    return format_odontologo_response(odontologo)

def registrar_odontologo(db: Session, data: OdontologoCreate, current_user: Usuario) -> dict:
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )

    if db.query(Personal).filter(Personal.dni == data.dni).first():
        raise HTTPException(status_code=400, detail="El DNI ya se encuentra registrado en el sistema")
    if db.query(Usuario).filter(Usuario.username == data.username).first():
        raise HTTPException(status_code=400, detail=f"El nombre de usuario '{data.username}' ya está en uso")
    if db.query(Odontologo).filter(Odontologo.colegiatura == data.colegiatura).first():
        raise HTTPException(status_code=400, detail="El número de colegiatura ya está registrado")
    if db.query(Personal).filter(Personal.correo == data.correo).first():
        raise HTTPException(status_code=400, detail="El correo electrónico ya está en uso")
    if db.query(Personal).filter(Personal.telefono == data.telefono).first():
        raise HTTPException(status_code=400, detail="El número de teléfono ya está en uso")

    esp_upper = data.especialidad.strip().upper()
    try:
        esp_enum = EspecialidadEnum(esp_upper)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Especialidad no válida. Permitidas: {[e.value for e in EspecialidadEnum]}",
        )

    now = datetime.now(timezone.utc)

    # 1. Crear Usuario
    new_usuario = Usuario(
        username=data.username,
        password=get_password_hash(data.password),
        activo=True,
        user_role=UserRoleEnum.ODONTOLOGO,
        fecha_registro=now,
    )

    # 2. Crear Odontólogo (hereda de Personal vía Joined-Table Inheritance;
    # SQLAlchemy inserta primero en `personal` y luego en `odontologo` sin duplicar filas)
    new_odontologo = Odontologo(
        dni=data.dni,
        nombres=data.nombres,
        apellidos=data.apellidos,
        telefono=data.telefono,
        correo=data.correo,
        activo=True,
        fecha_registro=now,
        colegiatura=data.colegiatura,
        especialidad=esp_enum,
        username=data.username,
    )

    try:
        db.add(new_usuario)
        db.flush()
        db.add(new_odontologo)
        db.commit()
        db.refresh(new_odontologo)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al registrar odontólogo: {str(e)}")

    return format_odontologo_response(new_odontologo)

def actualizar_odontologo(db: Session, dni: str, data: OdontologoUpdate, current_user: Usuario) -> dict:
    odontologo = db.query(Odontologo).filter(Odontologo.dni == dni).first()
    if not odontologo:
        raise HTTPException(status_code=404, detail=f"Odontólogo con DNI {dni} no encontrado")

    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    is_admin = role_val in ("SYSTEM_ADMIN", "ADMIN")
    if not is_admin and odontologo.username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )
    
    if not is_admin:
        if data.colegiatura is not None or data.especialidad is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los administradores pueden modificar la colegiatura y especialidad"
            )
        
    if data.correo and data.correo != odontologo.correo:
        if db.query(Personal).filter(Personal.correo == data.correo, Personal.dni != dni).first():
            raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado por otro personal")
        odontologo.correo = data.correo

    if data.telefono and data.telefono != odontologo.telefono:
        if db.query(Personal).filter(Personal.telefono == data.telefono, Personal.dni != dni).first():
            raise HTTPException(status_code=400, detail="El teléfono ya está registrado por otro personal")
        odontologo.telefono = data.telefono

    if data.colegiatura and data.colegiatura != odontologo.colegiatura:
        if db.query(Odontologo).filter(Odontologo.colegiatura == data.colegiatura, Odontologo.dni != dni).first():
            raise HTTPException(status_code=400, detail="El número de colegiatura ya está registrado")
        odontologo.colegiatura = data.colegiatura

    if data.especialidad:
        esp_upper = data.especialidad.strip().upper()
        try:
            odontologo.especialidad = EspecialidadEnum(esp_upper)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Especialidad no válida. Permitidas: {[e.value for e in EspecialidadEnum]}")

    if data.nombres is not None:
        odontologo.nombres = data.nombres
    if data.apellidos is not None:
        odontologo.apellidos = data.apellidos
    if data.activo is not None and current_user.user_role == UserRoleEnum.SYSTEM_ADMIN:
        odontologo.activo = data.activo
        if odontologo.usuario:
            odontologo.usuario.activo = data.activo

    try:
        db.commit()
        db.refresh(odontologo)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar odontólogo: {str(e)}")
    return format_odontologo_response(odontologo)

def cambiar_estado_odontologo(db: Session, dni: str, activo: bool, current_user: Usuario) -> dict:
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )

    odontologo = db.query(Odontologo).filter(Odontologo.dni == dni).first()
    if not odontologo:
        raise HTTPException(status_code=404, detail=f"Odontólogo con DNI {dni} no encontrado")

    # Odontologo hereda directamente de Personal (Joined-Table Inheritance)
    odontologo.activo = activo
    if odontologo.usuario:
        odontologo.usuario.activo = activo

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al cambiar estado del odontólogo: {str(e)}")
    estado_texto = "activado" if activo else "desactivado"
    return {"message": f"El odontólogo con DNI {dni} ha sido {estado_texto} exitosamente"}


def _normalizar_dia_semana(dia: str) -> DiaSemanaEnum:
    """Normaliza un día de la semana (mayúsculas y sin tildes) a DiaSemanaEnum."""
    sin_tildes = "".join(
        ch
        for ch in unicodedata.normalize("NFD", dia.strip())
        if unicodedata.category(ch) != "Mn"
    )
    try:
        return DiaSemanaEnum(sin_tildes.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Día de la semana no válido. Permitidos: {[d.value for d in DiaSemanaEnum]}",
        )


def listar_horarios_odontologo(db: Session, dni: str) -> List[HorarioPersonal]:
    odontologo = db.query(Odontologo).filter(Odontologo.dni == dni).first()
    if not odontologo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Odontólogo no encontrado",
        )

    return (
        db.query(HorarioPersonal)
        .filter(HorarioPersonal.dni == dni)
        .order_by(HorarioPersonal.dia_semana.asc(), HorarioPersonal.hora_inicio.asc())
        .all()
    )


def listar_horarios_odontologo_por_dia(
    db: Session, dni: str, dia: str
) -> List[HorarioPersonal]:
    odontologo = db.query(Odontologo).filter(Odontologo.dni == dni).first()
    if not odontologo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Odontólogo no encontrado",
        )

    dia_enum = _normalizar_dia_semana(dia)
    return (
        db.query(HorarioPersonal)
        .filter(
            HorarioPersonal.dni == dni,
            HorarioPersonal.dia_semana == dia_enum,
        )
        .order_by(HorarioPersonal.hora_inicio.asc())
        .all()
    )