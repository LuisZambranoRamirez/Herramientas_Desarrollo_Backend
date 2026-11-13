
import re
from datetime import date, datetime
from typing import Optional, Union, Any

from pydantic import BaseModel, ConfigDict, field_validator
from app.core.security import validar_password_segura


def _vacio_a_none(v: Any) -> Any:
    """Convierte cadenas vacías o con espacios en None."""
    if isinstance(v, str) and not v.strip():
        return None
    return v


class PacienteBase(BaseModel):
    nombres: str
    apellidos: str
    telefono: Optional[str] = None
    correo: Optional[str] = None
    direccion: Optional[str] = None
    observaciones: Optional[str] = ""
    fecha_nacimiento: date

    @field_validator("telefono", "correo", "direccion", mode="before")
    @classmethod
    def normalizar_vacios(cls, v: Any) -> Any:
        return _vacio_a_none(v)

    @field_validator("nombres", "apellidos")
    @classmethod
    def validar_nombres_apellidos(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2 or len(clean) > 100:
            raise ValueError("Debe tener entre 2 y 100 caracteres.")
        if not re.fullmatch(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$", clean):
            raise ValueError("Solo se permiten letras y espacios.")
        return clean

    @field_validator("correo")
    @classmethod
    def validar_correo(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().lower()
            if not re.fullmatch(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", clean):
                raise ValueError("El formato del correo electrónico no es válido.")
            return clean
        return v

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if v and not re.fullmatch(r"\d{9}", v):
                raise ValueError(
                    "El teléfono debe contener exactamente 9 dígitos numéricos."
                )
        return v

    @field_validator("fecha_nacimiento")
    @classmethod
    def validar_fecha_nacimiento(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("La fecha de nacimiento no puede ser en el futuro.")
        return v


class PacienteCreate(PacienteBase):
    dni: str
    username: Optional[str] = None
    password: Optional[str] = None

    @field_validator("dni")
    @classmethod
    def validar_dni(cls, v: str) -> str:
        v = v.strip()
        if not re.fullmatch(r"\d{8}", v):
            raise ValueError(
                "El DNI debe contener exactamente 8 dígitos numéricos."
            )
        return v

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            return validar_password_segura(v)
        return v


class PacienteUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    direccion: Optional[str] = None
    observaciones: Optional[str] = None
    fecha_nacimiento: Optional[date] = None

    @field_validator("telefono", "correo", "direccion", mode="before")
    @classmethod
    def normalizar_vacios(cls, v: Any) -> Any:
        return _vacio_a_none(v)

    @field_validator("nombres", "apellidos")
    @classmethod
    def validar_nombres_apellidos(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if len(clean) < 2 or len(clean) > 100:
                raise ValueError("Debe tener entre 2 y 100 caracteres.")
            if not re.fullmatch(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$", clean):
                raise ValueError("Solo se permiten letras y espacios.")
            return clean
        return v

    @field_validator("correo")
    @classmethod
    def validar_correo(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().lower()
            if not re.fullmatch(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", clean):
                raise ValueError("El formato del correo electrónico no es válido.")
            return clean
        return v

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if v and not re.fullmatch(r"\d{9}", v):
                raise ValueError(
                    "El teléfono debe contener exactamente 9 dígitos numéricos."
                )
        return v

    @field_validator("fecha_nacimiento")
    @classmethod
    def validar_fecha_nacimiento(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("La fecha de nacimiento no puede ser en el futuro.")
        return v


class PacienteResponse(PacienteBase):
    dni: str
    username: str
    fecha_registro: datetime
    activo: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)
