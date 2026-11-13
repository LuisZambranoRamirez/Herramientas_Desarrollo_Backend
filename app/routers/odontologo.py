from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Usuario, UserRoleEnum
from app.core.dependencies import get_current_user, require_roles
from app.schemas.odontologo import (
    OdontologoCreate,
    OdontologoUpdate,
    OdontologoResponse,
    HorarioResponse,
)
from app.services import odontologo as odontologo_service

router = APIRouter(prefix="/odontologos", tags=["Odontólogos"])

@router.get("/especialidades", response_model=List[str])
def listar_especialidades(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna la lista de todas las especialidades odontológicas disponibles.
    """
    return odontologo_service.listar_especialidades()

@router.get("", response_model=List[OdontologoResponse])
def listar_odontologos(
    especialidad: Optional[str] = Query(None, description="Filtrar por especialidad"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    query: Optional[str] = Query(None, description="Búsqueda por nombre, apellido, DNI o colegiatura"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todos los odontólogos con sus datos personales y especialidad.
    """
    return odontologo_service.listar_odontologos(db, especialidad=especialidad, activo=activo, query=query)

@router.get("/me", response_model=OdontologoResponse)
def obtener_mi_perfil_odontologo(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna el perfil del odontólogo actualmente conectado.
    """
    return odontologo_service.obtener_perfil_odontologo(db, current_user)

@router.get("/{dni}", response_model=OdontologoResponse)
def obtener_odontologo_por_dni(
    dni: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene los datos detallados de un odontólogo por su DNI.
    """
    return odontologo_service.obtener_odontologo_por_dni(db, dni)

@router.post("", response_model=OdontologoResponse, status_code=status.HTTP_201_CREATED)
def registrar_odontologo(
    data: OdontologoCreate,
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo odontólogo en el sistema (Crea Usuario, Personal y Odontologo).
    Solo para Administradores.
    """
    return odontologo_service.registrar_odontologo(db, data, current_user)

@router.put("/{dni}", response_model=OdontologoResponse)
def actualizar_odontologo(
    dni: str,
    data: OdontologoUpdate,
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN, UserRoleEnum.ODONTOLOGO)),
    db: Session = Depends(get_db)
):
    """
    Actualiza la información de un odontólogo.
    Solo para Administradores o el propio Odontólogo.
    """
    return odontologo_service.actualizar_odontologo(db, dni, data, current_user)

@router.patch("/{dni}/estado")
def cambiar_estado_odontologo(
    dni: str,
    activo: bool = Query(..., description="Estado activo o inactivo"),
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Activa o desactiva a un odontólogo.
    Solo para Administradores.
    """
    return odontologo_service.cambiar_estado_odontologo(db, dni, activo, current_user)

@router.get("/{dni}/horarios", response_model=List[HorarioResponse])
def listar_horarios_odontologo(
    dni: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todos los horarios configurados de un odontólogo por su DNI.
    """
    return odontologo_service.listar_horarios_odontologo(db, dni)

@router.get("/{dni}/horarios/{dia}", response_model=List[HorarioResponse])
def listar_horarios_odontologo_por_dia(
    dni: str,
    dia: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista los horarios de un odontólogo para un día específico de la semana.
    """
    return odontologo_service.listar_horarios_odontologo_por_dia(db, dni, dia)
