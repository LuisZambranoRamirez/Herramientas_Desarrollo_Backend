from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.usuario import Usuario
from app.core.dependencies import get_current_user
from app.schemas.odontologo import (
    OdontologoCreate,
    OdontologoUpdate,
    OdontologoResponse
)
from app.services import odontologo as odontologo_service

router = APIRouter(prefix="/odontologos", tags=["Odontólogos"])

@router.get("/especialidades", response_model=List[str])
def listar_especialidades():
    """
    Retorna la lista de todas las especialidades odontológicas disponibles.
    """
    return odontologo_service.listar_especialidades()

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
    db: Session = Depends(get_db)
):
    """
    Obtiene los datos detallados de un odontólogo por su DNI.
    """
    return odontologo_service.obtener_odontologo_por_dni(db, dni)

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
    return odontologo_service.registrar_odontologo(db, data, current_user)

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
    return odontologo_service.actualizar_odontologo(db, dni, data, current_user)

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
    return odontologo_service.cambiar_estado_odontologo(db, dni, activo, current_user)
