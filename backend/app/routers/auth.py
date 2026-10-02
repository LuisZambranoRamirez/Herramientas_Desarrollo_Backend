from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.usuario import Usuario
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserResponse,
    RegistroPaciente,
    RegistroPacienteResponse
)
from app.core.dependencies import get_current_user
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Inicia sesión con username y password.
    Retorna accessToken y los datos del usuario autenticado.
    """
    return auth_service.iniciar_sesion(db, credentials)

@router.post("/register", response_model=RegistroPacienteResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegistroPaciente, db: Session = Depends(get_db)):
    """
    Registra un nuevo paciente y su respectivo usuario en el sistema.
    """
    return auth_service.registrar_paciente(db, data)

@router.get("/me", response_model=UserResponse)
def get_me(current_user: Usuario = Depends(get_current_user)):
    """Valida el Bearer token y retorna el perfil del usuario autenticado."""
    return current_user
