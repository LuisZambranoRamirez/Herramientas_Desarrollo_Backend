from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Usuario
from app.core.dependencies import get_current_user
from app.schemas.proveedor import ProveedorCreate, ProveedorUpdate, ProveedorResponse
from app.services import proveedor as proveedor_service

router = APIRouter(prefix="/proveedores", tags=["Proveedores"])

@router.get("", response_model=List[ProveedorResponse])
def listar_proveedores(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todos los proveedores registrados."""
    return proveedor_service.listar_proveedores(db, current_user)

@router.get("/{ruc}", response_model=ProveedorResponse)
def obtener_proveedor(
    ruc: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene los datos de un proveedor por su RUC."""
    return proveedor_service.obtener_proveedor_por_ruc(db, ruc, current_user)

@router.post("", response_model=ProveedorResponse, status_code=status.HTTP_201_CREATED)
def crear_proveedor(
    data: ProveedorCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registra un nuevo proveedor (Solo administradores)."""
    return proveedor_service.crear_proveedor(db, data, current_user)

@router.patch("/{ruc}", response_model=ProveedorResponse)
def actualizar_proveedor(
    ruc: str,
    data: ProveedorUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza la información de un proveedor."""
    return proveedor_service.actualizar_proveedor(db, ruc, data, current_user)

@router.delete("/{ruc}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_proveedor(
    ruc: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elimina un proveedor del sistema."""
    proveedor_service.eliminar_proveedor(db, ruc, current_user)
    return None
