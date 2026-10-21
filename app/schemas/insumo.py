import uuid
from datetime import date, datetime
from typing import Optional, Union, Any
from pydantic import BaseModel, ConfigDict, field_validator

class InsumoCreate(BaseModel):
    nombre: str
    stock: float
    stock_minimo: float
    fecha_vencimiento: Optional[date] = None

    @field_validator("stock", "stock_minimo")
    @classmethod
    def validar_cantidades(cls, v: float) -> float:
        if v < 0:
            raise ValueError("El stock no puede ser negativo.")
        return v

class InsumoUpdate(BaseModel):
    nombre: Optional[str] = None
    stock: Optional[float] = None
    stock_minimo: Optional[float] = None
    fecha_vencimiento: Optional[date] = None

    @field_validator("stock", "stock_minimo")
    @classmethod
    def validar_cantidades(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("El stock no puede ser negativo.")
        return v

class InsumoResponse(BaseModel):
    insumo_id: uuid.UUID
    nombre: str
    stock: float
    stock_minimo: float
    fecha_registro: Union[datetime, str]
    fecha_vencimiento: Optional[Union[date, str]] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("fecha_registro", mode="before")
    @classmethod
    def serialize_fecha(cls, v: Any) -> Any:
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    @field_validator("fecha_vencimiento", mode="before")
    @classmethod
    def serialize_vencimiento(cls, v: Any) -> Any:
        if isinstance(v, (date, datetime)):
            return v.isoformat()
        return v

class InsumoCompradoCreate(BaseModel):
    id_insumo: uuid.UUID
    id_proveedor: str
    cantidad: float
    precio_unitario: float

    @field_validator("cantidad", "precio_unitario")
    @classmethod
    def validar_positivos(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Debe ser mayor a cero.")
        return v

class InsumoCompradoResponse(BaseModel):
    insumo_comprado_id: uuid.UUID
    id_insumo: uuid.UUID
    id_proveedor: str
    cantidad: float
    precio_unitario: float
    fecha_registro: Union[datetime, str]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("fecha_registro", mode="before")
    @classmethod
    def serialize_fecha(cls, v: Any) -> Any:
        if isinstance(v, datetime):
            return v.isoformat()
        return v

class ConsumoInsumosCreate(BaseModel):
    id_agenda_tratamiento: uuid.UUID
    id_insumo: uuid.UUID
    cantidad: float

    @field_validator("cantidad")
    @classmethod
    def validar_cantidad(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("La cantidad debe ser mayor a cero.")
        return v

class ConsumoInsumosResponse(BaseModel):
    consumo_insumos_id: uuid.UUID
    id_agenda_tratamiento: uuid.UUID
    id_insumo: uuid.UUID
    cantidad: float

    model_config = ConfigDict(from_attributes=True)
