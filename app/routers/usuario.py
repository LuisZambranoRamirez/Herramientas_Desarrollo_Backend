from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Usuario, UserRoleEnum
from app.core.dependencies import get_current_user, require_roles
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    OdontologoPublicResponse,
    CambiarRolRequest,
)
from app.services import usuario as usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("/dentists", response_model=List[OdontologoPublicResponse])
@router.get("/odontologos/activos", response_model=List[OdontologoPublicResponse])
def listar_odontologos_activos(
    db: Session = Depends(get_db)
):
    """
    Retorna la lista pública de odontólogos activos registrados en el sistema.
    Público: No requiere autenticación.
    """
    return usuario_service.listar_odontologos_activos(db)


@router.get("", response_model=List[UsuarioResponse])
def listar_usuarios(
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Lista todos los usuarios del sistema (Solo Administradores).
    """
    return usuario_service.listar_usuarios(db, current_user)


@router.get("/{username}", response_model=UsuarioResponse)
def obtener_usuario(
    username: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el perfil y detalles de un usuario específico.
    """
    return usuario_service.obtener_usuario(db, username, current_user)


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    data: UsuarioCreate,
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo usuario en la plataforma asegurando datos de contacto y relaciones (Solo Administradores).
    """
    return usuario_service.crear_usuario(db, data, current_user)


@router.patch("/{username}/rol", response_model=UsuarioResponse)
@router.put("/{username}/rol", response_model=UsuarioResponse)
def cambiar_rol_usuario(
    username: str,
    data: CambiarRolRequest,
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Cambia el rol de un usuario y sincroniza de forma consistente
    su perfil y relaciones en la base de datos (Solo Administradores).
    """
    return usuario_service.cambiar_rol_usuario(
        db=db,
        username=username,
        nuevo_rol_str=data.user_role,
        current_user=current_user,
        especialidad=data.especialidad,
        colegiatura=data.colegiatura
    )


@router.patch("/{username}", response_model=UsuarioResponse)
def actualizar_usuario(
    username: str,
    data: UsuarioUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza datos de un usuario existente manteniendo consistencia en sus relaciones.
    """
    return usuario_service.actualizar_usuario(db, username, data, current_user)


@router.patch("/{username}/toggle-status", response_model=UsuarioResponse)
def toggle_status(
    username: str,
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Alterna el estado activo/inactivo de un usuario (Solo Administradores).
    """
    return usuario_service.toggle_status_usuario(db, username, current_user)


@router.delete("/{username}", status_code=status.HTTP_200_OK)
def eliminar_usuario(
    username: str,
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Elimina definitivamente un usuario del sistema (Solo Administradores).
    Impide auto-eliminación y valida citas médicas activas.
    """
    return usuario_service.eliminar_usuario(db, username, current_user)
