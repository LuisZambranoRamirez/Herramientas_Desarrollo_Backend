import re
from datetime import date, datetime
from typing import Union, Any, Optional
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from app.core.security import verify_password, get_password_hash, validar_password_segura

# Esquema para la solicitud de inicio de sesión
class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validar_username(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("El nombre de usuario o correo es obligatorio.")
        return clean

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("La contraseña es obligatoria.")
        return v

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

    @field_validator("username")
    @classmethod
    def validar_username(cls, v: str) -> str:
        clean = v.strip().lower()
        if len(clean) < 3:
            raise ValueError("El nombre de usuario debe tener al menos 3 caracteres.")
        return clean

    @field_validator("nombres", "apellidos")
    @classmethod
    def validar_nombres_apellidos(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2 or len(clean) > 100:
            raise ValueError("Debe tener entre 2 y 100 caracteres.")
        if not re.fullmatch(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$", clean):
            raise ValueError("Solo se permiten letras y espacios.")
        return clean

    @field_validator("correo")
    @classmethod
    def validar_correo(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.fullmatch(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", clean):
            raise ValueError("El formato del correo electrónico no es válido.")
        return clean

    @field_validator("fecha_nacimiento", mode="before")
    @classmethod
    def validar_fecha_nacimiento(cls, v: Any) -> Any:
        if isinstance(v, str):
            clean = v.strip().split("T")[0]
            parsed = date.fromisoformat(clean)
            if parsed > date.today():
                raise ValueError("La fecha de nacimiento no puede ser en el futuro.")
            return parsed
        if isinstance(v, date) and v > date.today():
            raise ValueError("La fecha de nacimiento no puede ser en el futuro.")
        return v

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        return validar_password_segura(v)

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
