from typing import Callable, Set
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload
import jwt

from app.core.database import get_db
from app.models.models import Usuario, UserRoleEnum
from app.core.security import decode_access_token

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Usuario:
    """Valida el Bearer Token JWT y retorna el usuario autenticado desde la BD."""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales de autenticación inválidas o expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        # pyrefly: ignore [bad-assignment]
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except (jwt.PyJWTError, Exception):
        raise credentials_exception

    # Consulta optimizada con carga ansiosa (joinedload) para evitar datos vacíos en relaciones
    user = (
        db.query(Usuario)
        .options(
            joinedload(Usuario.odontologo),
            joinedload(Usuario.paciente)
        )
        .filter(Usuario.username == username)
        .first()
    )

    if user is None:
        raise credentials_exception
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo en el sistema"
        )
    return user


def require_roles(*allowed_roles: UserRoleEnum) -> Callable[[Usuario], Usuario]:
    """
    Fábrica de dependencias RBAC para verificar que el usuario autenticado
    tenga uno de los roles permitidos.
    Lanza HTTP 401 si no está autenticado (vía get_current_user).
    Lanza HTTP 403 si el rol no tiene permisos suficientes.
    """
    allowed_values: Set[str] = set()
    for r in allowed_roles:
        val = r.value if hasattr(r, "value") else str(r)
        allowed_values.add(val.upper())
        if val.upper() == "SYSTEM_ADMIN":
            allowed_values.add("ADMIN")

    def role_checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        user_role = getattr(current_user, "user_role", None)
        role_str = (
            user_role.value if hasattr(user_role, "value") else str(user_role)
        ).upper()

        if role_str not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para realizar esta acción",
            )
        return current_user

    return role_checker


require_admin = require_roles(UserRoleEnum.SYSTEM_ADMIN)
require_clinical = require_roles(UserRoleEnum.SYSTEM_ADMIN, UserRoleEnum.ODONTOLOGO)
