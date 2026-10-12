from datetime import date, time, datetime
from typing import Optional, Union, Any
from pydantic import BaseModel, ConfigDict, field_validator

# Esquema para odontólogo resumido en las citas
class OdontologoSimpleResponse(BaseModel):
    dni: str
    nombres: str
    apellidos: str
    especialidad: str
    colegiatura: str

    model_config = ConfigDict(from_attributes=True)

# Esquema para paciente resumido en las citas
class PacienteSimpleResponse(BaseModel):
    dni: str
    nombres: str
    apellidos: str
    telefono: Optional[str] = None
    correo: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Esquema para solicitar creación de una cita
class CitaCreate(BaseModel):
    dni_odontologo: str
    fecha: date
    hora: Union[time, str]
    motivo_consulta: str
    dni_paciente: Optional[str] = None  # Opcional: si el usuario es paciente se toma de su sesión

    @field_validator("hora", mode="before")
    @classmethod
    def parse_hora(cls, v: Any) -> Any:
        if isinstance(v, str):
            # Soporta formato "HH:MM" o "HH:MM:SS"
            parts = v.strip().split(":")
            if len(parts) >= 2:
                hour = int(parts[0])
                minute = int(parts[1])
                second = int(parts[2]) if len(parts) > 2 else 0
                return time(hour, minute, second)
        return v

# Esquema para actualizar datos de una cita
class CitaUpdate(BaseModel):
    fecha: Optional[date] = None
    hora: Optional[Union[time, str]] = None
    motivo_consulta: Optional[str] = None
    diagnostico: Optional[str] = None

    @field_validator("hora", mode="before")
    @classmethod
    def parse_hora_update(cls, v: Any) -> Any:
        if isinstance(v, str):
            parts = v.strip().split(":")
            if len(parts) >= 2:
                return time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
        return v

# Esquema para cambiar solo el estado de la cita
class CitaEstadoUpdate(BaseModel):
    estado: str  # PROGRAMADA, CONFIRMADA, ATENDIDA, CANCELADA, NO_ASISTIO, REPROGRAMADA, EN_PROCESO
    diagnostico: Optional[str] = None

# Esquema completo de respuesta de cita
class CitaResponse(BaseModel):
    cita_id: str
    dni_paciente: str
    dni_odontologo: str
    fecha: Union[date, str]
    hora: Union[time, str]
    motivo_consulta: str
    diagnostico: Optional[str] = None
    estado: str
    fecha_registro: Union[datetime, str]
    paciente: Optional[PacienteSimpleResponse] = None
    odontologo: Optional[OdontologoSimpleResponse] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("fecha", mode="before")
    @classmethod
    def serialize_fecha(cls, v: Any) -> Any:
        if isinstance(v, date):
            return v.isoformat()
        return v

    @field_validator("hora", mode="before")
    @classmethod
    def serialize_hora(cls, v: Any) -> Any:
        if isinstance(v, time):
            return v.strftime("%H:%M:%S")
        return str(v)

    @field_validator("fecha_registro", mode="before")
    @classmethod
    def serialize_fecha_registro(cls, v: Any) -> Any:
        if isinstance(v, datetime):
            return v.isoformat()
        return v
