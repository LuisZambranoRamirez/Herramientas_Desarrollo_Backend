from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.connection import get_db
from app.models.usuario import Usuario
from app.models.paciente import Paciente
from app.routers.auth import get_current_user
from app.core.security import get_password_hash
from app.schemas.paciente import (
    PacienteCreate,
    PacienteUpdate,
    PacienteResponse
)

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])

def format_paciente_response(p: Paciente) -> dict:
    return {
        "dni": p.dni,
        "username": p.username,
        "nombres": p.nombres,
        "apellidos": p.apellidos,
        "telefono": p.telefono,
        "correo": p.correo,
        "direccion": p.direccion,
        "observaciones": p.observaciones or "",
        "fecha_nacimiento": p.fecha_nacimiento,
        "fecha_registro": p.fecha_registro,
        "activo": p.usuario.activo if p.usuario else True
    }

@router.get("", response_model=List[PacienteResponse])
def listar_pacientes(
    query: Optional[str] = Query(None, description="Búsqueda por DNI, nombres, apellidos o correo"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todos los pacientes registrados en el sistema.
    Solo accesible para Administradores y Odontólogos.
    """
    if current_user.user_role not in ["SYSTEM_ADMIN", "ODONTOLOGO"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver el listado de pacientes"
        )

    q = db.query(Paciente).join(Usuario, Paciente.username == Usuario.username)

    if query:
        search_filter = f"%{query.strip()}%"
        q = q.filter(
            or_(
                Paciente.dni.ilike(search_filter),
                Paciente.nombres.ilike(search_filter),
                Paciente.apellidos.ilike(search_filter),
                Paciente.correo.ilike(search_filter)
            )
        )

    if activo is not None:
        q = q.filter(Usuario.activo == activo)

    pacientes = q.order_by(Paciente.apellidos.asc(), Paciente.nombres.asc()).all()
    return [format_paciente_response(p) for p in pacientes]

@router.get("/me", response_model=PacienteResponse)
def obtener_mi_perfil_paciente(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna la ficha del paciente conectado actualmente.
    """
    paciente = db.query(Paciente).filter(Paciente.username == current_user.username).first()
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró una ficha de paciente asociada a este usuario"
        )
    return format_paciente_response(paciente)

@router.get("/{dni}", response_model=PacienteResponse)
def obtener_paciente_por_dni(
    dni: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene los datos clínicos y de contacto de un paciente por su DNI.
    """
    paciente = db.query(Paciente).filter(Paciente.dni == dni).first()
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente con DNI {dni} no encontrado"
        )

    # Si es paciente, solo puede ver su propia información
    if current_user.user_role == "PACIENTE" and paciente.username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para consultar información de otro paciente"
        )

    return format_paciente_response(paciente)

@router.post("", response_model=PacienteResponse, status_code=status.HTTP_201_CREATED)
def registrar_paciente(
    data: PacienteCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo paciente desde recepción o administración.
    """
    if current_user.user_role not in ["SYSTEM_ADMIN", "ODONTOLOGO"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo personal autorizado puede dar de alta a nuevos pacientes"
        )

    # Validaciones de unicidad
    if db.query(Paciente).filter(Paciente.dni == data.dni).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El DNI ya se encuentra registrado"
        )

    username = data.username or data.correo or data.dni
    if db.query(Usuario).filter(Usuario.username == username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El nombre de usuario '{username}' ya está en uso"
        )

    if data.correo and db.query(Paciente).filter(Paciente.correo == data.correo).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado"
        )

    if data.telefono and db.query(Paciente).filter(Paciente.telefono == data.telefono).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de teléfono ya está registrado"
        )

    raw_password = data.password or data.dni
    now = datetime.utcnow()

    new_user = Usuario(
        username=username,
        password=get_password_hash(raw_password),
        activo=True,
        user_role="PACIENTE",
        fecha_registro=now
    )

    new_paciente = Paciente(
        dni=data.dni,
        username=username,
        nombres=data.nombres,
        apellidos=data.apellidos,
        telefono=data.telefono,
        correo=data.correo,
        direccion=data.direccion,
        observaciones=data.observaciones or "",
        fecha_nacimiento=data.fecha_nacimiento,
        fecha_registro=now
    )

    try:
        db.add(new_user)
        db.add(new_paciente)
        db.commit()
        db.refresh(new_user)
        db.refresh(new_paciente)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar paciente: {str(e)}"
        )

    return format_paciente_response(new_paciente)

@router.put("/{dni}", response_model=PacienteResponse)
def actualizar_paciente(
    dni: str,
    data: PacienteUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza la información de un paciente.
    """
    paciente = db.query(Paciente).filter(Paciente.dni == dni).first()
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente con DNI {dni} no encontrado"
        )

    # Validar permisos
    if current_user.user_role == "PACIENTE" and paciente.username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar los datos de otro paciente"
        )

    # Validar unicidad si cambia correo o teléfono
    if data.correo and data.correo != paciente.correo:
        if db.query(Paciente).filter(Paciente.correo == data.correo, Paciente.dni != dni).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado por otro paciente"
            )
        paciente.correo = data.correo

    if data.telefono and data.telefono != paciente.telefono:
        if db.query(Paciente).filter(Paciente.telefono == data.telefono, Paciente.dni != dni).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El número de teléfono ya está registrado por otro paciente"
            )
        paciente.telefono = data.telefono

    if data.nombres is not None:
        paciente.nombres = data.nombres
    if data.apellidos is not None:
        paciente.apellidos = data.apellidos
    if data.direccion is not None:
        paciente.direccion = data.direccion
    if data.observaciones is not None:
        paciente.observaciones = data.observaciones
    if data.fecha_nacimiento is not None:
        paciente.fecha_nacimiento = data.fecha_nacimiento

    db.commit()
    db.refresh(paciente)
    return format_paciente_response(paciente)

@router.delete("/{dni}")
def desactivar_paciente(
    dni: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Desactiva la cuenta de un paciente en el sistema (baja lógica).
    Solo para Administradores.
    """
    if current_user.user_role != "SYSTEM_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden desactivar pacientes"
        )

    paciente = db.query(Paciente).filter(Paciente.dni == dni).first()
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente con DNI {dni} no encontrado"
        )

    if paciente.usuario:
        paciente.usuario.activo = False
        db.commit()

    return {"message": f"El paciente con DNI {dni} ha sido desactivado exitosamente"}
