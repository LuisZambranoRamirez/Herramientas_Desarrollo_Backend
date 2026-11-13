from datetime import datetime, timezone
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.models import Usuario, UserRoleEnum
from app.core.security import get_password_hash
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse


def _to_usuario_response(u: Usuario) -> UsuarioResponse:
    nombre_completo = None
    correo = None
    telefono = None

    if getattr(u, "odontologo", None):
        odon = u.odontologo
        nombre_completo = f"{odon.nombres} {odon.apellidos}".strip()
        correo = odon.correo
        telefono = odon.telefono
    elif getattr(u, "paciente", None):
        pac = u.paciente
        nombre_completo = f"{pac.nombres} {pac.apellidos}".strip()
        correo = pac.correo
        telefono = pac.telefono

    role_val = u.user_role.value if hasattr(u.user_role, "value") else str(u.user_role)

    return UsuarioResponse(
        username=u.username,
        user_role=role_val,
        activo=u.activo,
        fecha_registro=u.fecha_registro,
        nombre_completo=nombre_completo or u.username,
        correo=correo,
        telefono=telefono,
        ultimo_acceso=None
    )


def listar_usuarios(db: Session, current_user: Usuario) -> List[UsuarioResponse]:
    """Lista todos los usuarios del sistema (Solo administradores)."""
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )

    usuarios = (
        db.query(Usuario)
        .options(
            joinedload(Usuario.odontologo),
            joinedload(Usuario.paciente)
        )
        .order_by(Usuario.fecha_registro.desc())
        .all()
    )
    return [_to_usuario_response(u) for u in usuarios]


def obtener_usuario(db: Session, username: str, current_user: Usuario) -> UsuarioResponse:
    """Obtiene el detalle de un usuario por su username (Solo admin o propio usuario)."""
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN") and current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )

    usuario = (
        db.query(Usuario)
        .options(
            joinedload(Usuario.odontologo),
            joinedload(Usuario.paciente)
        )
        .filter(Usuario.username == username)
        .first()
    )
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario '{username}' no encontrado."
        )
    return _to_usuario_response(usuario)


def crear_usuario(db: Session, data: UsuarioCreate, current_user: Usuario) -> UsuarioResponse:
    """Crea un nuevo usuario en la base de datos (Solo administradores)."""
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )

    clean_username = data.username.strip()
    existente = db.query(Usuario).filter(Usuario.username == clean_username).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El nombre de usuario '{clean_username}' ya existe en el sistema."
        )

    try:
        role_enum = UserRoleEnum(data.user_role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol '{data.user_role}' no es válido."
        )

    hashed_pw = get_password_hash(data.password)
    nuevo_usuario = Usuario(
        username=clean_username,
        password=hashed_pw,
        activo=data.activo,
        user_role=role_enum,
        fecha_registro=datetime.now(timezone.utc),
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return _to_usuario_response(nuevo_usuario)


def actualizar_usuario(db: Session, username: str, data: UsuarioUpdate, current_user: Usuario) -> UsuarioResponse:
    """Actualiza campos de un usuario existente."""
    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario '{username}' no encontrado."
        )

    if data.user_role is not None:
        try:
            usuario.user_role = UserRoleEnum(data.user_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol '{data.user_role}' no es válido."
            )

    if data.activo is not None:
        usuario.activo = data.activo

    if data.password:
        usuario.password = get_password_hash(data.password)

    db.commit()
    db.refresh(usuario)

    return _to_usuario_response(usuario)


def toggle_status_usuario(db: Session, username: str, current_user: Usuario) -> UsuarioResponse:
    """Alterna el estado activo de un usuario."""
    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario '{username}' no encontrado."
        )

    usuario.activo = not usuario.activo
    db.commit()
    db.refresh(usuario)

    return _to_usuario_response(usuario)


def eliminar_usuario(db: Session, username: str, current_user: Usuario) -> None:
    """Elimina un usuario del sistema."""
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propio usuario en sesión activa."
        )

    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario '{username}' no encontrado."
        )

    db.delete(usuario)
    db.commit()