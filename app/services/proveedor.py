from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Proveedor, InsumoComprado, Usuario
from app.schemas.proveedor import ProveedorCreate, ProveedorUpdate

def listar_proveedores(db: Session, current_user: Usuario) -> List[Proveedor]:
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN", "ODONTOLOGO"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )
    return db.query(Proveedor).order_by(Proveedor.nombre.asc()).all()

def obtener_proveedor_por_ruc(db: Session, ruc: str, current_user: Usuario) -> Proveedor:
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN", "ODONTOLOGO"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )
    prov = db.query(Proveedor).filter(Proveedor.ruc == ruc).first()
    if not prov:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proveedor no encontrado."
        )
    return prov

def crear_proveedor(db: Session, data: ProveedorCreate, current_user: Usuario) -> Proveedor:
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )

    if db.query(Proveedor).filter(Proveedor.ruc == data.ruc).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un proveedor con el RUC {data.ruc}."
        )

    nuevo_prov = Proveedor(
        ruc=data.ruc,
        nombre=data.nombre,
        telefono=data.telefono,
        fecha_registro=datetime.now(timezone.utc)
    )

    try:
        db.add(nuevo_prov)
        db.commit()
        db.refresh(nuevo_prov)
        return nuevo_prov
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al registrar el proveedor."
        )

def actualizar_proveedor(db: Session, ruc: str, data: ProveedorUpdate, current_user: Usuario) -> Proveedor:
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )

    prov = obtener_proveedor_por_ruc(db, ruc, current_user)

    if data.nombre is not None:
        prov.nombre = data.nombre
    if data.telefono is not None:
        prov.telefono = data.telefono

    try:
        db.commit()
        db.refresh(prov)
        return prov
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al actualizar el proveedor."
        )

def eliminar_proveedor(db: Session, ruc: str, current_user: Usuario) -> dict:
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )

    prov = obtener_proveedor_por_ruc(db, ruc, current_user)

    tiene_compras = (
        db.query(InsumoComprado.insumo_comprado_id)
        .filter(InsumoComprado.id_proveedor == ruc)
        .first()
        is not None
    )
    if tiene_compras:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar el proveedor porque tiene compras de insumos registradas."
        )

    try:
        db.delete(prov)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al eliminar el proveedor."
        )

    return {"message": f"Proveedor con RUC {ruc} eliminado exitosamente."}

