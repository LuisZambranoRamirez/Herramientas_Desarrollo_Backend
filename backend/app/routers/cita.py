from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.usuario import Usuario
from app.core.dependencies import get_current_user
from app.schemas.cita import (
    CitaCreate,
    CitaEstadoUpdate,
    CitaResponse,
    OdontologoSimpleResponse
)
from app.services import cita as cita_service

router = APIRouter(prefix="/citas", tags=["Citas Odontológicas"])

@router.get("/odontologos", response_model=List[OdontologoSimpleResponse])
def listar_odontologos_disponibles(db: Session = Depends(get_db)):
    """
    Lista todos los odontólogos registrados y activos para seleccionar al agendar citas.
    """
    return cita_service.listar_odontologos_disponibles(db)

@router.post("", response_model=CitaResponse, status_code=status.HTTP_201_CREATED)
def agendar_cita(
    data: CitaCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Agenda una nueva cita odontológica.
    - Si el usuario es rol PACIENTE, se enlaza automáticamente a su DNI.
    - Si es ADMIN u ODONTOLOGO, requiere el campo 'dni_paciente'.
    """
    return cita_service.agendar_cita(db, data, current_user)

@router.get("/mis-citas", response_model=List[CitaResponse])
def mis_citas(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna el listado de citas del usuario conectado:
    - Pacientes ven sus citas médicas agendadas.
    - Odontólogos ven las citas asignadas a ellos.
    - Administradores ven todas las citas.
    """
    return cita_service.listar_mis_citas(db, current_user)

@router.get("", response_model=List[CitaResponse])
def listar_todas_las_citas(
    fecha: Optional[date] = Query(None, description="Filtrar por fecha"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    dni_paciente: Optional[str] = Query(None, description="Filtrar por DNI paciente"),
    dni_odontologo: Optional[str] = Query(None, description="Filtrar por DNI odontólogo"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listado general de citas con filtros para administración y personal clínico.
    """
    return cita_service.listar_citas(
        db,
        current_user,
        fecha=fecha,
        estado=estado,
        dni_paciente=dni_paciente,
        dni_odontologo=dni_odontologo
    )

@router.get("/{cita_id}", response_model=CitaResponse)
def obtener_detalle_cita(
    cita_id: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene los datos detallados de una cita."""
    return cita_service.obtener_detalle_cita(db, cita_id, current_user)

@router.patch("/{cita_id}/estado", response_model=CitaResponse)
def actualizar_estado_cita(
    cita_id: str,
    data: CitaEstadoUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza el estado de una cita (CONFIRMADA, ATENDIDA, CANCELADA, etc.).
    """
    return cita_service.actualizar_estado_cita(db, cita_id, data, current_user)

@router.patch("/{cita_id}/cancelar", response_model=CitaResponse)
def cancelar_cita(
    cita_id: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancela una cita de forma directa.
    """
    return cita_service.cancelar_cita(db, cita_id, current_user)
