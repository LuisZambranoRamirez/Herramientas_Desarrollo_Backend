from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.usuario import Usuario
from app.core.dependencies import get_current_user
from app.schemas.paciente import (
    PacienteCreate,
    PacienteUpdate,
    PacienteResponse
)
from app.services import paciente as paciente_service

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])

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
    return paciente_service.listar_pacientes(db, current_user, query=query, activo=activo)

@router.get("/me", response_model=PacienteResponse)
def obtener_mi_perfil_paciente(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna la ficha del paciente conectado actualmente.
    """
    return paciente_service.obtener_perfil_paciente(db, current_user)

@router.get("/{dni}", response_model=PacienteResponse)
def obtener_paciente_por_dni(
    dni: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene los datos clínicos y de contacto de un paciente por su DNI.
    """
    return paciente_service.obtener_paciente_por_dni(db, dni, current_user)

@router.post("", response_model=PacienteResponse, status_code=status.HTTP_201_CREATED)
def registrar_paciente(
    data: PacienteCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo paciente desde recepción o administración.
    """
    return paciente_service.registrar_paciente(db, data, current_user)

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
    return paciente_service.actualizar_paciente(db, dni, data, current_user)

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
    return paciente_service.desactivar_paciente(db, dni, current_user)
