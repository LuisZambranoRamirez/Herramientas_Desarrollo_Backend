import re
import uuid
from datetime import datetime, time
from typing import Optional, Union, Any
from pydantic import BaseModel, ConfigDict, field_validator

class TratamientoCreate(BaseModel):
    dni_paciente: str
    dni_odontologo: str
    observaciones: str
    precio: float
    tratamiento: str
    estado: Optional[str] = "INICIADO"

    @field_validator("dni_paciente", "dni_odontologo")
    @classmethod
    def validar_dnis(cls, v: str) -> str:
        if v:
            v = v.strip()
            if not re.fullmatch(r"^\d{8}$", v):
                raise ValueError("El DNI debe contener exactamente 8 dígitos numéricos.")
        return v

    @field_validator("precio")
    @classmethod
    def validar_precio(cls, v: float) -> float:
        if v < 0:
            raise ValueError("El precio no puede ser negativo.")
        return v

class TratamientoUpdate(BaseModel):
    observaciones: Optional[str] = None
    precio: Optional[float] = None
    tratamiento: Optional[str] = None
    estado: Optional[str] = None

    @field_validator("precio")
    @classmethod
    def validar_precio(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("El precio no puede ser negativo.")
        return v

class TratamientoResponse(BaseModel):
    tratamiento_paciente_id: uuid.UUID
    dni_paciente: str
    dni_odontologo: str
    observaciones: str
    precio: float
    tratamiento: str
    estado: str
    fecha_registro: Union[datetime, str]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("tratamiento", "estado", mode="before")
    @classmethod
    def serialize_enums(cls, v: Any) -> str:
        if hasattr(v, "value"):
            return str(v.value)
        return str(v)

    @field_validator("fecha_registro", mode="before")
    @classmethod
    def serialize_fecha(cls, v: Any) -> Any:
        if isinstance(v, datetime):
            return v.isoformat()
        return v

class AgendaTratamientoCreate(BaseModel):
    id_tratamiento_paciente: uuid.UUID
    dia_semana: str
    hora_inicio: Union[time, str]
    hora_fin: Union[time, str]

    @field_validator("hora_inicio", "hora_fin", mode="before")
    @classmethod
    def parse_horas(cls, v: Any) -> Any:
        if isinstance(v, str):
            parts = v.strip().split(":")
            if len(parts) >= 2:
                hour = int(parts[0])
                minute = int(parts[1])
                second = int(parts[2]) if len(parts) > 2 else 0
                return time(hour, minute, second)
        return v

class AgendaTratamientoResponse(BaseModel):
    agenda_tratamientos_id: uuid.UUID
    id_tratamiento_paciente: uuid.UUID
    dia_semana: str
    hora_inicio: Union[time, str]
    hora_fin: Union[time, str]
    fecha_registro: Union[datetime, str]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("dia_semana", mode="before")
    @classmethod
    def serialize_dia(cls, v: Any) -> str:
        if hasattr(v, "value"):
            return str(v.value)
        return str(v)

    @field_validator("hora_inicio", "hora_fin", mode="before")
    @classmethod
    def serialize_time(cls, v: Any) -> str:
        if isinstance(v, time):
            return v.strftime("%H:%M:%S")
        return str(v)

    @field_validator("fecha_registro", mode="before")
    @classmethod
    def serialize_fecha(cls, v: Any) -> Any:
        if isinstance(v, datetime):
            return v.isoformat()
        return v
