import re
from datetime import datetime
from typing import Optional, Union, Any
from pydantic import BaseModel, ConfigDict, field_validator

class ProveedorCreate(BaseModel):
    ruc: str
    nombre: str
    telefono: str

    @field_validator("ruc")
    @classmethod
    def validar_ruc(cls, v: str) -> str:
        if v:
            v = v.strip()
            if not re.fullmatch(r"^\d{11}$", v):
                raise ValueError("El RUC debe contener exactamente 11 dígitos numéricos.")
        return v

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: str) -> str:
        if v:
            v = v.strip()
            if not re.fullmatch(r"^\d{9}$", v):
                raise ValueError("El teléfono debe contener exactamente 9 dígitos numéricos.")
        return v

class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if v and not re.fullmatch(r"^\d{9}$", v):
                raise ValueError("El teléfono debe contener exactamente 9 dígitos numéricos.")
        return v

class ProveedorResponse(BaseModel):
    ruc: str
    nombre: str
    telefono: str
    fecha_registro: Union[datetime, str]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("fecha_registro", mode="before")
    @classmethod
    def serialize_fecha(cls, v: Any) -> Any:
        if isinstance(v, datetime):
            return v.isoformat()
        return v
