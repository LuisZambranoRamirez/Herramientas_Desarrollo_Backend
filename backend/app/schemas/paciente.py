from datetime import date, datetime
from typing import Optional, Union, Any
from pydantic import BaseModel, ConfigDict, field_validator

class PacienteBase(BaseModel):
    nombres: str
    apellidos: str
    telefono: Optional[str] = None
    correo: Optional[str] = None
    direccion: Optional[str] = None
    observaciones: Optional[str] = ""
    fecha_nacimiento: date

class PacienteCreate(PacienteBase):
    dni: str
    username: Optional[str] = None  # Si no se envía se usa el correo o el dni
    password: Optional[str] = None  # Contraseña inicial (por defecto el DNI si no se proporciona)

class PacienteUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    direccion: Optional[str] = None
    observaciones: Optional[str] = None
    fecha_nacimiento: Optional[date] = None

class PacienteResponse(PacienteBase):
    dni: str
    username: str
    fecha_registro: Union[datetime, str]
    activo: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)

    @field_validator("fecha_nacimiento", mode="before")
    @classmethod
    def serialize_fecha_nacimiento(cls, v: Any) -> Any:
        if isinstance(v, date):
            return v.isoformat()
        return v

    @field_validator("fecha_registro", mode="before")
    @classmethod
    def serialize_fecha_registro(cls, v: Any) -> Any:
        if isinstance(v, datetime):
            return v.isoformat()
        return v
