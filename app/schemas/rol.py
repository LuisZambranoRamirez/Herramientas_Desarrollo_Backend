from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.models import PermisosEnum, UserRoleEnum


def normalizar_role_str(v: Any) -> str:
    """Normaliza y valida que el rol pertenezca a UserRoleEnum."""
    raw = v.value if hasattr(v, "value") else str(v)
    clean = raw.strip().upper()
    permitidos = [r.value for r in UserRoleEnum]
    if not clean:
        raise ValueError(
            f"El rol no puede estar vacío. Roles permitidos en el ENUM actual: {permitidos}."
        )
    try:
        return UserRoleEnum(clean).value
    except ValueError:
        raise ValueError(
            f"Rol '{raw}' no válido. Solo se permiten roles del ENUM actual: {permitidos}."
        )


def normalizar_permiso_str(v: Any) -> str:
    """Normaliza y valida que el permiso pertenezca a PermisosEnum."""
    raw = v.value if hasattr(v, "value") else str(v)
    clean = raw.strip().upper()
    # Compatibilidad con el literal 'ACTULIZAR' definido en permisos_enum de PostgreSQL
    if clean == "ACTUALIZAR":
        clean = PermisosEnum.ACTULIZAR.value
    permitidos = [p.value for p in PermisosEnum]
    if not clean:
        raise ValueError(
            f"El permiso no puede estar vacío. Permisos permitidos: {permitidos}."
        )
    try:
        return PermisosEnum(clean).value
    except ValueError:
        raise ValueError(
            f"Permiso '{raw}' no válido. Los permisos permitidos son: {permitidos} (también se acepta 'ACTUALIZAR')."
        )


class RoleResponse(BaseModel):
    role: str = Field(..., description="Identificador del rol del sistema (UserRoleEnum)")
    descripcion: str = Field(..., description="Descripción funcional del rol en la clínica")
    permisos: Optional[str] = Field(
        None,
        description="Permiso asignado en role_permisos (LEER, ACTULIZAR, ELIMINAR, CREAR) o None si no ha sido configurado",
    )
    modulos: List[str] = Field(
        default_factory=list,
        description="Módulos del sistema asociados al alcance del rol",
    )
    configurado: bool = Field(
        False,
        description="Indica si existe un registro persistido en la tabla role_permisos",
    )

    model_config = ConfigDict(from_attributes=True)

    @field_validator("role", mode="before")
    @classmethod
    def serialize_role(cls, v: Any) -> str:
        if hasattr(v, "value"):
            return str(v.value)
        return str(v)

    @field_validator("permisos", mode="before")
    @classmethod
    def serialize_permisos(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if hasattr(v, "value"):
            return str(v.value)
        return str(v)


class RolePermisoCreate(BaseModel):
    role: str = Field(
        ...,
        description="Nombre del rol perteneciente al ENUM actual: SYSTEM_ADMIN, ODONTOLOGO o PACIENTE",
    )
    permisos: str = Field(
        ...,
        description="Permiso a asignar al rol: LEER, ACTULIZAR (o ACTUALIZAR), ELIMINAR, CREAR",
    )

    @field_validator("role")
    @classmethod
    def validar_role(cls, v: str) -> str:
        return normalizar_role_str(v)

    @field_validator("permisos")
    @classmethod
    def validar_permisos(cls, v: str) -> str:
        return normalizar_permiso_str(v)


class RolePermisoUpdate(BaseModel):
    permisos: str = Field(
        ...,
        description="Nuevo permiso a asignar al rol: LEER, ACTULIZAR (o ACTUALIZAR), ELIMINAR, CREAR",
    )

    @field_validator("permisos")
    @classmethod
    def validar_permisos(cls, v: str) -> str:
        return normalizar_permiso_str(v)

