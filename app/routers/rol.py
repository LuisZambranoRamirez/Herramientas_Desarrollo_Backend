from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import UserRoleEnum, Usuario
from app.schemas.rol import RolePermisoCreate, RolePermisoUpdate, RoleResponse
from app.services import rol as rol_service

router = APIRouter(prefix="/roles", tags=["Roles y Permisos"])


def require_system_admin(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """Valida que el usuario autenticado tenga rol SYSTEM_ADMIN."""
    role_val = (
        current_user.user_role.value
        if hasattr(current_user.user_role, "value")
        else str(current_user.user_role)
    )
    if role_val != UserRoleEnum.SYSTEM_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores (SYSTEM_ADMIN) tienen acceso a la gestión de roles y permisos.",
        )
    return current_user


@router.get("", response_model=List[RoleResponse])
def listar_roles(
    current_user: Usuario = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    """
    Lista todos los roles disponibles en el sistema con su descripción y permisos asociados.
    Solo para administradores (SYSTEM_ADMIN).
    """
    return rol_service.obtener_roles(db)


@router.get("/{role}", response_model=RoleResponse)
def obtener_detalle_rol(
    role: str,
    current_user: Usuario = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    """
    Obtiene el detalle y configuración de permisos de un rol específico.
    Solo para administradores (SYSTEM_ADMIN).
    """
    return rol_service.obtener_permisos_por_rol(db, role)


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def asignar_permisos_rol(
    data: RolePermisoCreate,
    current_user: Usuario = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    """
    Registra o actualiza la asignación de permisos para un rol perteneciente al ENUM del sistema.
    Solo para administradores (SYSTEM_ADMIN).
    """
    return rol_service.guardar_o_actualizar_permisos_rol(db, data.role, data)


@router.put("/{role}/permisos", response_model=RoleResponse)
def actualizar_permisos_rol(
    role: str,
    data: RolePermisoUpdate,
    current_user: Usuario = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    """
    Modifica los permisos asignados a un rol existente.
    Solo para administradores (SYSTEM_ADMIN).
    """
    return rol_service.guardar_o_actualizar_permisos_rol(
        db,
        role,
        data,
        not_found_on_unknown_role=True,
    )

