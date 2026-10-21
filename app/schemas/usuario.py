from datetime import datetime
from typing import Optional, Union, Any
from pydantic import BaseModel, ConfigDict, field_validator


class UsuarioResponse(BaseModel):
    username: str
    user_role: str
    activo: bool
    fecha_registro: Union[datetime, str]
    nombre_completo: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    ultimo_acceso: Optional[Union[datetime, str]] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("user_role", mode="before")
    @classmethod
    def serialize_user_role(cls, v: Any) -> str:
        if hasattr(v, "value"):
            return str(v.value)
        return str(v)

    @field_validator("fecha_registro", mode="before")
    @classmethod
    def serialize_fecha_registro(cls, v: Any) -> Any:
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class UsuarioCreate(BaseModel):
    username: str
    password: str
    user_role: str = "PACIENTE"
    activo: bool = True
    nombre_completo: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None


class UsuarioUpdate(BaseModel):
    user_role: Optional[str] = None
    activo: Optional[bool] = None
    nombre_completo: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    password: Optional[str] = None
