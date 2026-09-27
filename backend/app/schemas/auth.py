from datetime import date, datetime
from typing import Union, Any, Optional
from pydantic import BaseModel, ConfigDict, field_validator
from app.core.security import verify_password, get_password_hash

# Esquema para la solicitud de inicio de sesión
class LoginRequest(BaseModel):
    username: str
    password: str

# Esquema para representar la información pública del usuario
class UserResponse(BaseModel):
    username: str
    user_role: str
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

# Esquema de respuesta para POST /api/auth/login
class LoginResponse(BaseModel):
    accessToken: str
    user: UserResponse

# Esquema para datos contenidos en el token
class TokenPayload(BaseModel):
    sub: Optional[str] = None
    user_role: Optional[str] = None
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

# Esquema de respuesta para registro de paciente
class RegistroPacienteResponse(BaseModel):
    message: str = "Paciente registrado exitosamente"
    accessToken: Optional[str] = None
    user: UserResponse
