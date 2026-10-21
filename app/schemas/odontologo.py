import re
from datetime import datetime
from typing import Optional, Union, Any, List
from pydantic import BaseModel, ConfigDict, field_validator

class OdontologoBase(BaseModel):
    nombres: str
    apellidos: str
    telefono: str
    correo: str
    colegiatura: str
    especialidad: str

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

class OdontologoUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    colegiatura: Optional[str] = None
    especialidad: Optional[str] = None
    activo: Optional[bool] = None

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
