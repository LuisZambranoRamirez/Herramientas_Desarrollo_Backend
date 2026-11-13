import re
import uuid
from datetime import datetime, time
from typing import Optional, Union, Any, List
from pydantic import BaseModel, ConfigDict, field_validator
from app.core.security import validar_password_segura

class OdontologoBase(BaseModel):
    nombres: str
    apellidos: str
    telefono: str
    correo: str
    colegiatura: str
    especialidad: str

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
    def validar_correo(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.fullmatch(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", clean):
            raise ValueError("El formato del correo electrónico no es válido.")
        return clean

    @field_validator("colegiatura")
    @classmethod
    def validar_colegiatura(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("La colegiatura es obligatoria.")
        return clean

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: str) -> str:
        if v:
            v = v.strip()
            if not re.fullmatch(r"^\d{9}$", v):
                raise ValueError("El teléfono debe contener exactamente 9 dígitos numéricos.")
        return v

class OdontologoCreate(OdontologoBase):
    dni: str
    username: str
    password: str

    @field_validator("dni")
    @classmethod
    def validar_dni(cls, v: str) -> str:
        if v:
            v = v.strip()
            if not re.fullmatch(r"^\d{8}$", v):
                raise ValueError("El DNI debe contener exactamente 8 dígitos numéricos.")
        return v

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        return validar_password_segura(v)

class OdontologoUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    colegiatura: Optional[str] = None
    especialidad: Optional[str] = None
    activo: Optional[bool] = None

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
            if v and not re.fullmatch(r"^\d{9}$", v):
                raise ValueError("El teléfono debe contener exactamente 9 dígitos numéricos.")
        return v

class OdontologoResponse(OdontologoBase):
    dni: str
    username: str
    activo: bool
    fecha_registro: Union[datetime, str]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("especialidad", mode="before")
    @classmethod
    def serialize_especialidad(cls, v: Any) -> str:
        if hasattr(v, "value"):
            return str(v.value)
        return str(v)

    @field_validator("fecha_registro", mode="before")
    @classmethod
    def serialize_fecha_registro(cls, v: Any) -> Any:
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class HorarioResponse(BaseModel):
    horario_odontologo_id: uuid.UUID
    dni: str
    dia_semana: str
    hora_inicio: Union[time, str]
    hora_fin: Union[time, str]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("dia_semana", mode="before")
    @classmethod
    def serialize_dia_semana(cls, v: Any) -> str:
        if hasattr(v, "value"):
            return str(v.value)
        return str(v)

    @field_validator("hora_inicio", "hora_fin", mode="before")
    @classmethod
    def serialize_time(cls, v: Any) -> str:
        if isinstance(v, time):
            return v.strftime("%H:%M:%S")
        return str(v)
