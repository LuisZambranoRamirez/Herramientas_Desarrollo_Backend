import uuid
from datetime import datetime
from typing import Union, Any
from pydantic import BaseModel, ConfigDict, field_validator

class PagoCreate(BaseModel):
    id_tratamiento_paciente: uuid.UUID
    monto: float
    metodo_pago: str

    @field_validator("monto")
    @classmethod
    def validar_monto(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("El monto debe ser mayor a cero.")
        return v

    @field_validator("metodo_pago")
    @classmethod
    def validar_metodo(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if v_clean not in ("efectivo", "digital"):
            raise ValueError("El método de pago debe ser 'efectivo' o 'digital'.")
        return v_clean

class PagoResponse(BaseModel):
    pago_id: uuid.UUID
    id_tratamiento_paciente: uuid.UUID
    monto: float
    metodo_pago: str
    fecha_registro: Union[datetime, str]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("metodo_pago", mode="before")
    @classmethod
    def serialize_metodo(cls, v: Any) -> str:
        if hasattr(v, "value"):
            return str(v.value)
        return str(v)

    @field_validator("fecha_registro", mode="before")
    @classmethod
    def serialize_fecha(cls, v: Any) -> Any:
        if isinstance(v, datetime):
            return v.isoformat()
        return v
