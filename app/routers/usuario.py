from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Usuario
from app.core.dependencies import get_current_user
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.services import usuario as usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("", response_model=List[UsuarioResponse])
def listar_usuarios(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todos los usuarios del sistema.
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
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo usuario en la plataforma.
    """
    return usuario_service.crear_usuario(db, data, current_user)


@router.patch("/{username}", response_model=UsuarioResponse)
def actualizar_usuario(
    username: str,
    data: UsuarioUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza datos de un usuario existente.
    """
    return usuario_service.actualizar_usuario(db, username, data, current_user)


@router.patch("/{username}/toggle-status", response_model=UsuarioResponse)
def toggle_status(
    username: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Alterna el estado activo/inactivo de un usuario.
    """
    return usuario_service.toggle_status_usuario(db, username, current_user)


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    username: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Elimina un usuario del sistema.
    """
    usuario_service.eliminar_usuario(db, username, current_user)
    return None
