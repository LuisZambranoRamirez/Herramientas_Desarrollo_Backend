import re
from datetime import datetime
from typing import Optional, Union, Any
from pydantic import BaseModel, ConfigDict, field_validator
from app.core.security import validar_password_segura


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

    @field_validator("username")
    @classmethod
    def validar_username(cls, v: str) -> str:
        clean = v.strip().lower()
        if len(clean) < 3:
            raise ValueError("El nombre de usuario debe tener al menos 3 caracteres.")
        if not re.fullmatch(r"^[a-zA-Z0-9._-]+$", clean):
            raise ValueError("El nombre de usuario solo puede contener letras, números, puntos, guiones y guiones bajos.")
        return clean

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        return validar_password_segura(v)

    @field_validator("nombre_completo")
    @classmethod
    def validar_nombre_completo(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if not clean:
                return None
            if len(clean) < 2 or len(clean) > 100:
                raise ValueError("El nombre completo debe tener entre 2 y 100 caracteres.")
            if not re.fullmatch(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$", clean):
                raise ValueError("El nombre solo debe contener letras y espacios.")
            return clean
        return v

    @field_validator("correo")
    @classmethod
    def validar_correo(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().lower()
            if not clean:
                return None
            if not re.fullmatch(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", clean):
                raise ValueError("El formato del correo electrónico no es válido.")
            return clean
        return v

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if not clean:
                return None
            if not re.fullmatch(r"^\d{9}$", clean):
                raise ValueError("El teléfono debe contener exactamente 9 dígitos numéricos.")
            return clean
        return v


class UsuarioUpdate(BaseModel):
    user_role: Optional[str] = None
    activo: Optional[bool] = None
    nombre_completo: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    password: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validar_password_segura(v)
        return v

    @field_validator("nombre_completo")
    @classmethod
    def validar_nombre_completo(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if not clean:
                return None
            if len(clean) < 2 or len(clean) > 100:
                raise ValueError("El nombre completo debe tener entre 2 y 100 caracteres.")
            if not re.fullmatch(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$", clean):
                raise ValueError("El nombre solo debe contener letras y espacios.")
            return clean
        return v

    @field_validator("correo")
    @classmethod
    def validar_correo(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().lower()
            if not clean:
                return None
            if not re.fullmatch(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", clean):
                raise ValueError("El formato del correo electrónico no es válido.")
            return clean
        return v

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if not clean:
                return None
            if not re.fullmatch(r"^\d{9}$", clean):
                raise ValueError("El teléfono debe contener exactamente 9 dígitos numéricos.")
            return clean
        return v
