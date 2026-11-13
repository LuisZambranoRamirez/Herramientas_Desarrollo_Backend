import re
from datetime import date, datetime
from typing import Union, Any, Optional
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from app.core.security import verify_password, get_password_hash

# Esquema para la solicitud de inicio de sesión
class LoginRequest(BaseModel):
    username: str
    password: str

# Esquema para representar la información pública del usuario
class UserResponse(BaseModel):
    username: str
    user_role: str
    role: Optional[str] = None
    activo: bool
    fecha_registro: Union[datetime, str]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("user_role", mode="before")
    @classmethod
    def serialize_user_role(cls, v: Any) -> str:
        if hasattr(v, "value"):
            return str(v.value)
        return str(v)

    @field_validator("fecha_registro", mode="before")
    @classmethod
    def serialize_fecha_registro(cls, v: Any) -> Any:
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    @model_validator(mode="after")
    def sync_role(self) -> "UserResponse":
        if not self.role and self.user_role:
            self.role = self.user_role
        return self

# Esquema de respuesta para POST /api/auth/login
class LoginResponse(BaseModel):
    accessToken: str
    user: UserResponse
    role: Optional[str] = None

    @model_validator(mode="after")
    def sync_role(self) -> "LoginResponse":
        if not self.role and self.user:
            self.role = self.user.role or self.user.user_role
        return self

# Esquema para datos contenidos en el token
class TokenPayload(BaseModel):
    sub: Optional[str] = None
    user_role: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None

# Esquema para registro de paciente
class RegistroPaciente(BaseModel):
    username: str
    password: str
    dni: str
    nombres: str
    apellidos: str
    telefono: str
    correo: str
    fecha_nacimiento: Union[date, str]
    direccion: Optional[str] = None
    role: Optional[str] = None
    user_role: Optional[str] = None

    @field_validator("role", "user_role")
    @classmethod
    def validar_no_inyeccion_rol(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().upper()
            if clean in ("ADMIN", "SYSTEM_ADMIN", "ODONTOLOGO", "DOCTOR"):
                raise ValueError("No está permitido asignar roles con privilegios durante el registro público.")
        return v

    @field_validator("dni")
    @classmethod
    def validar_dni(cls, v: str) -> str:
        if v:
            v = v.strip()
            if not re.fullmatch(r"^\d{8}$", v):
                raise ValueError("El DNI debe contener exactamente 8 dígitos numéricos.")
        return v

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: str) -> str:
        if v:
            v = v.strip()
            if not re.fullmatch(r"^\d{9}$", v):
                raise ValueError("El teléfono debe contener exactamente 9 dígitos numéricos.")
        return v

# Esquema de respuesta para registro de paciente
class RegistroPacienteResponse(BaseModel):
    message: str = "Paciente registrado exitosamente"
    accessToken: Optional[str] = None
    user: UserResponse
    role: Optional[str] = None

    @model_validator(mode="after")
    def sync_role(self) -> "RegistroPacienteResponse":
        if not self.role and self.user:
            self.role = self.user.role or self.user.user_role
        return self
