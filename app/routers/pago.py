import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Usuario
from app.core.dependencies import get_current_user
from app.schemas.pago import PagoCreate, PagoResponse
from app.services import pago as pago_service

router = APIRouter(prefix="/pagos", tags=["Pagos"])

@router.get("", response_model=List[PagoResponse])
def listar_pagos(
    tratamiento_id: Optional[uuid.UUID] = Query(None, description="Filtrar por ID de tratamiento"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todos los comprobantes de pago registrados."""
    return pago_service.listar_pagos(db, current_user, tratamiento_id=tratamiento_id)

@router.get("/tratamiento/{tratamiento_id}", response_model=List[PagoResponse])
def listar_pagos_por_tratamiento(
    tratamiento_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista los pagos asociados a un tratamiento en particular."""
    return pago_service.listar_pagos(db, current_user, tratamiento_id=tratamiento_id)

@router.get("/{pago_id}", response_model=PagoResponse)
def obtener_pago(
    pago_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene los detalles de un pago específico."""
    return pago_service.obtener_pago_por_id(db, pago_id, current_user)

@router.post("", response_model=PagoResponse, status_code=status.HTTP_201_CREATED)
def registrar_pago(
    data: PagoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registra un nuevo pago (Solo administradores)."""
    return pago_service.registrar_pago(db, data, current_user)
