from datetime import date, datetime
from typing import Optional, Union, Any
from pydantic import BaseModel, ConfigDict, field_validator

def _vacio_a_none(v: Any) -> Any:
    """Convierte '' en None: direccion, telefono y correo son UNIQUE en la BD,
    así que dos pacientes con '' chocarían entre sí."""
    if isinstance(v, str) and not v.strip():
        return None
    return v.strip() if isinstance(v, str) else v

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

    @field_validator("telefono", "correo", "direccion", mode="before")
    @classmethod
    def normalizar_vacios(cls, v: Any) -> Any:
        return _vacio_a_none(v)

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
