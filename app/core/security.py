from datetime import datetime, timedelta, timezone
import re
from typing import Any, Optional
import jwt
from passlib.context import CryptContext
from app.core.config import config

# Contexto de encriptación con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def validar_password_segura(password: str) -> str:
    """
    Valida que una contraseña cumpla con los estándares de seguridad:
    - Mínimo 8 caracteres.
    - Al menos una letra mayúscula (A-Z).
    - Al menos una letra minúscula (a-z).
    - Al menos un dígito numérico (0-9).
    """
    if not isinstance(password, str):
        raise ValueError("La contraseña debe ser una cadena de texto.")
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres de longitud.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("La contraseña debe contener al menos una letra mayúscula (A-Z).")
    if not re.search(r"[a-z]", password):
        raise ValueError("La contraseña debe contener al menos una letra minúscula (a-z).")
    if not re.search(r"[0-9]", password):
        raise ValueError("La contraseña debe contener al menos un número (0-9).")
    return password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña en texto plano coincide con el hash almacenado."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera el hash bcrypt de una contraseña."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Genera un token JWT firmado con fecha de expiración."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decodifica y valida un token JWT."""
    return jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
