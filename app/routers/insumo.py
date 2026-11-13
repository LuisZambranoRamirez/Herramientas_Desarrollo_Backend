import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Usuario, UserRoleEnum
from app.core.dependencies import get_current_user, require_roles
from app.schemas.insumo import (
    InsumoCreate,
    InsumoUpdate,
    InsumoResponse,
    InsumoCompradoCreate,
    InsumoCompradoResponse,
    ConsumoInsumosCreate,
    ConsumoInsumosResponse
)
from app.services import insumo as insumo_service

router = APIRouter(prefix="/insumos", tags=["Insumos"])

@router.get("", response_model=List[InsumoResponse])
def listar_insumos(
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN, UserRoleEnum.ODONTOLOGO)),
    db: Session = Depends(get_db)
):
    """Lista todos los insumos médicos del inventario."""
    return insumo_service.listar_insumos(db, current_user)

@router.get("/stock-bajo", response_model=List[InsumoResponse])
def listar_insumos_stock_bajo(
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN, UserRoleEnum.ODONTOLOGO)),
    db: Session = Depends(get_db)
):
    """Lista los insumos que están por debajo o igual a su stock mínimo."""
    return insumo_service.listar_insumos(db, current_user, stock_bajo=True)

@router.get("/consumos", response_model=List[ConsumoInsumosResponse])
def listar_consumos(
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN, UserRoleEnum.ODONTOLOGO)),
    db: Session = Depends(get_db)
):
    """Lista el historial de consumos de insumos."""
    return insumo_service.listar_consumos(db, current_user)

@router.post("/consumos", response_model=ConsumoInsumosResponse, status_code=status.HTTP_201_CREATED)
def registrar_consumo(
    data: ConsumoInsumosCreate,
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN, UserRoleEnum.ODONTOLOGO)),
    db: Session = Depends(get_db)
):
    """Registra el consumo de insumo en una sesión de tratamiento y descuenta stock."""
    return insumo_service.registrar_consumo(db, data, current_user)

@router.get("/compras", response_model=List[InsumoCompradoResponse])
def listar_todas_las_compras(
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    """Lista el historial general de compras de insumos."""
    return insumo_service.listar_compras(db, None, current_user)

@router.post("/compras", response_model=InsumoCompradoResponse, status_code=status.HTTP_201_CREATED)
def registrar_compra(
    data: InsumoCompradoCreate,
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    """Registra una compra a proveedor y añade unidades al stock del insumo."""
    return insumo_service.registrar_compra(db, data, current_user)

@router.get("/{insumo_id}", response_model=InsumoResponse)
def obtener_insumo(
    insumo_id: uuid.UUID,
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN, UserRoleEnum.ODONTOLOGO)),
    db: Session = Depends(get_db)
):
    """Obtiene el detalle de un insumo."""
    return insumo_service.obtener_insumo_por_id(db, insumo_id, current_user)

@router.post("", response_model=InsumoResponse, status_code=status.HTTP_201_CREATED)
def crear_insumo(
    data: InsumoCreate,
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    """Crea un nuevo insumo (Solo administradores)."""
    return insumo_service.crear_insumo(db, data, current_user)

@router.patch("/{insumo_id}", response_model=InsumoResponse)
def actualizar_insumo(
    insumo_id: uuid.UUID,
    data: InsumoUpdate,
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    """Actualiza los datos o existencias de un insumo."""
    return insumo_service.actualizar_insumo(db, insumo_id, data, current_user)

@router.delete("/{insumo_id}", status_code=status.HTTP_200_OK)
def eliminar_insumo(
    insumo_id: uuid.UUID,
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    """Elimina un insumo si no tiene compras ni consumos registrados."""
    return insumo_service.eliminar_insumo(db, insumo_id, current_user)

@router.get("/{insumo_id}/compras", response_model=List[InsumoCompradoResponse])
def listar_compras_insumo(
    insumo_id: uuid.UUID,
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    """Lista el historial de compras de un insumo específico."""
    return insumo_service.listar_compras(db, insumo_id, current_user)
