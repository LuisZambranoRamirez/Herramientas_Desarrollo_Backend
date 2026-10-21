import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Usuario
from app.core.dependencies import get_current_user
from app.schemas.tratamiento import (
    TratamientoCreate,
    TratamientoUpdate,
    TratamientoResponse,
    AgendaTratamientoCreate,
    AgendaTratamientoResponse
)
from app.services import tratamiento as tratamiento_service

router = APIRouter(prefix="/tratamientos", tags=["Tratamientos"])

@router.get("", response_model=List[TratamientoResponse])
def listar_tratamientos(
    paciente_dni: Optional[str] = Query(None, description="Filtrar por DNI del paciente"),
    estado: Optional[str] = Query(None, description="Filtrar por estado del tratamiento"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista los tratamientos médicos según rol y filtros."""
    return tratamiento_service.listar_tratamientos(db, current_user, paciente_dni=paciente_dni, estado=estado)

@router.get("/paciente/{dni}", response_model=List[TratamientoResponse])
def listar_por_paciente(
    dni: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todos los tratamientos de un paciente específico."""
    return tratamiento_service.listar_tratamientos(db, current_user, paciente_dni=dni)

@router.get("/estado/{estado}", response_model=List[TratamientoResponse])
def listar_por_estado(
    estado: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista tratamientos filtrando por su estado."""
    return tratamiento_service.listar_tratamientos(db, current_user, estado=estado)

@router.get("/{tratamiento_id}", response_model=TratamientoResponse)
def obtener_tratamiento(
    tratamiento_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene los detalles de un tratamiento específico."""
    return tratamiento_service.obtener_tratamiento_por_id(db, tratamiento_id, current_user)

@router.post("", response_model=TratamientoResponse, status_code=status.HTTP_201_CREATED)
def crear_tratamiento(
    data: TratamientoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registra un nuevo plan de tratamiento para un paciente."""
    return tratamiento_service.crear_tratamiento(db, data, current_user)

@router.patch("/{tratamiento_id}", response_model=TratamientoResponse)
def actualizar_tratamiento(
    tratamiento_id: uuid.UUID,
    data: TratamientoUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza observaciones, precio, tipo o estado de un tratamiento."""
    return tratamiento_service.actualizar_tratamiento(db, tratamiento_id, data, current_user)

@router.get("/{tratamiento_id}/agenda", response_model=List[AgendaTratamientoResponse])
def listar_agenda(
    tratamiento_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista los horarios y sesiones agendadas de un tratamiento."""
    return tratamiento_service.listar_agenda(db, tratamiento_id, current_user)

@router.post("/agenda", response_model=AgendaTratamientoResponse, status_code=status.HTTP_201_CREATED)
def crear_agenda(
    data: AgendaTratamientoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Agrega una sesión recurrente o fecha a la agenda del tratamiento."""
    return tratamiento_service.crear_agenda(db, data, current_user)
