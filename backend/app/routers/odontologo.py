from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.connection import get_db
from app.models.usuario import Usuario
from app.models.personal import Personal
from app.models.odontologo import Odontologo, Especialidad
from app.core.dependencies import get_current_user
from app.core.security import get_password_hash
from app.schemas.odontologo import (
    OdontologoCreate,
    OdontologoUpdate,
    OdontologoResponse
)

router = APIRouter(prefix="/odontologos", tags=["Odontólogos"])

def format_odontologo_response(o: Odontologo) -> dict:
    esp = o.especialidad.value if hasattr(o.especialidad, "value") else str(o.especialidad)
    nombres = o.personal.nombres if o.personal else ""
    apellidos = o.personal.apellidos if o.personal else ""
    telefono = o.personal.telefono if o.personal else ""
    correo = o.personal.correo if o.personal else ""
    activo = o.personal.activo if o.personal else True
    fecha_reg = o.personal.fecha_registro if o.personal else datetime.utcnow()

    return {
        "dni": o.dni,
        "username": o.username,
        "nombres": nombres,
        "apellidos": apellidos,
        "telefono": telefono,
        "correo": correo,
        "colegiatura": o.colegiatura,
        "especialidad": esp,
        "activo": activo,
        "fecha_registro": fecha_reg
    }

@router.get("/especialidades", response_model=List[str])
def listar_especialidades():
    """
    Retorna la lista de todas las especialidades odontológicas disponibles.
    """
    return [e.value for e in Especialidad]

@router.get("", response_model=List[OdontologoResponse])
def listar_odontologos(
    especialidad: Optional[str] = Query(None, description="Filtrar por especialidad"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    query: Optional[str] = Query(None, description="Búsqueda por nombre, apellido, DNI o colegiatura"),
    db: Session = Depends(get_db)
):
    """
    Lista todos los odontólogos con sus datos personales y especialidad.
    """
    q = db.query(Odontologo).join(Personal, Odontologo.dni == Personal.dni)

    if especialidad:
        q = q.filter(Odontologo.especialidad == especialidad.upper())

    if activo is not None:
        q = q.filter(Personal.activo == activo)

    if query:
        search_filter = f"%{query.strip()}%"
        q = q.filter(
            or_(
                Odontologo.dni.ilike(search_filter),
                Odontologo.colegiatura.ilike(search_filter),
                Personal.nombres.ilike(search_filter),
                Personal.apellidos.ilike(search_filter)
            )
        )

    odontologos = q.order_by(Personal.apellidos.asc(), Personal.nombres.asc()).all()
    return [format_odontologo_response(o) for o in odontologos]

@router.get("/me", response_model=OdontologoResponse)
def obtener_mi_perfil_odontologo(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna el perfil del odontólogo actualmente conectado.
    """
    odontologo = db.query(Odontologo).filter(Odontologo.username == current_user.username).first()
    if not odontologo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró un perfil de odontólogo asociado a tu cuenta"
        )
    return format_odontologo_response(odontologo)

@router.get("/{dni}", response_model=OdontologoResponse)
def obtener_odontologo_por_dni(
    dni: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene los datos detallados de un odontólogo por su DNI.
    """
    odontologo = db.query(Odontologo).filter(Odontologo.dni == dni).first()
    if not odontologo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Odontólogo con DNI {dni} no encontrado"
        )
    return format_odontologo_response(odontologo)

@router.post("", response_model=OdontologoResponse, status_code=status.HTTP_201_CREATED)
def registrar_odontologo(
    data: OdontologoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo odontólogo en el sistema (Crea Usuario, Personal y Odontologo).
    Solo para Administradores.
    """
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
    if esp_upper not in [e.value for e in Especialidad]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Especialidad no válida. Permitidas: {[e.value for e in Especialidad]}"
        )

    now = datetime.utcnow()

    # 1. Crear Personal
    new_personal = Personal(
        dni=data.dni,
        nombres=data.nombres,
        apellidos=data.apellidos,
        telefono=data.telefono,
        correo=data.correo,
        activo=True,
        fecha_registro=now
    )

    # 2. Crear Usuario
    new_usuario = Usuario(
        username=data.username,
        password=get_password_hash(data.password),
        activo=True,
        user_role="ODONTOLOGO",
        fecha_registro=now
    )

    # 3. Crear Odontólogo
    new_odontologo = Odontologo(
        dni=data.dni,
        colegiatura=data.colegiatura,
        especialidad=esp_upper,
        username=data.username
    )

    try:
        db.add(new_personal)
        db.add(new_usuario)
        db.add(new_odontologo)
        db.commit()
        db.refresh(new_odontologo)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar odontólogo: {str(e)}"
        )

    return format_odontologo_response(new_odontologo)

@router.put("/{dni}", response_model=OdontologoResponse)
def actualizar_odontologo(
    dni: str,
    data: OdontologoUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza la información de un odontólogo.
    Solo para Administradores o el propio Odontólogo.
    """
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

    personal = odontologo.personal
    if not personal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de datos personales no encontrado"
        )

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
        if esp_upper not in [e.value for e in Especialidad]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Especialidad no válida. Permitidas: {[e.value for e in Especialidad]}"
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

@router.patch("/{dni}/estado")
def cambiar_estado_odontologo(
    dni: str,
    activo: bool = Query(..., description="Estado activo o inactivo"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Activa o desactiva a un odontólogo.
    Solo para Administradores.
    """
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

    if odontologo.personal:
        odontologo.personal.activo = activo
    if odontologo.usuario:
        odontologo.usuario.activo = activo

    db.commit()
    estado_texto = "activado" if activo else "desactivado"
    return {"message": f"El odontólogo con DNI {dni} ha sido {estado_texto} exitosamente"}
