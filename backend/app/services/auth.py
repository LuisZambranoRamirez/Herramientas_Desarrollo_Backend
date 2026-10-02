from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.models.paciente import Paciente
from app.schemas.auth import LoginRequest, RegistroPaciente
from app.core.security import verify_password, get_password_hash, create_access_token

def iniciar_sesion(db: Session, credentials: LoginRequest) -> dict:
    """Valida las credenciales y genera el token de acceso del usuario."""
    user = db.query(Usuario).filter(Usuario.username == credentials.username).first()

    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    role_str = user.user_role.value if hasattr(user.user_role, "value") else str(user.user_role)
    token = create_access_token(data={"sub": user.username, "user_role": role_str})

    return {
        "accessToken": token,
        "user": user
    }

def registrar_paciente(db: Session, data: RegistroPaciente) -> dict:
    """Crea el usuario y el paciente asociado, y genera su token de acceso."""
    # 1. Validar que el username no exista
    if db.query(Usuario).filter(Usuario.username == data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya se encuentra registrado"
        )

    # 2. Validar que el DNI no exista
    if db.query(Paciente).filter(Paciente.dni == data.dni).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El DNI ya se encuentra registrado"
        )

    # 3. Validar que el correo no esté en uso
    if db.query(Paciente).filter(Paciente.correo == data.correo).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya se encuentra registrado"
        )

    # 4. Validar que el teléfono no esté en uso (si se proporciona)
    if data.telefono and db.query(Paciente).filter(Paciente.telefono == data.telefono).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de teléfono ya se encuentra registrado"
        )

    # Parsear fecha_nacimiento si viene como string
    if isinstance(data.fecha_nacimiento, str):
        try:
            fecha_nac = datetime.strptime(data.fecha_nacimiento, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha de nacimiento inválido (debe ser YYYY-MM-DD)"
            )
    else:
        fecha_nac = data.fecha_nacimiento

    now = datetime.utcnow()

    # 5. Crear la entidad Usuario
    new_user = Usuario(
        username=data.username,
        password=get_password_hash(data.password),
        activo=True,
        user_role="PACIENTE",
        fecha_registro=now
    )

    # 6. Crear la entidad Paciente asociada
    new_paciente = Paciente(
        dni=data.dni,
        username=data.username,
        nombres=data.nombres,
        apellidos=data.apellidos,
        direccion=data.direccion,
        telefono=data.telefono,
        correo=data.correo,
        observaciones="",
        fecha_nacimiento=fecha_nac,
        fecha_registro=now
    )

    try:
        db.add(new_user)
        db.add(new_paciente)
        db.commit()
        db.refresh(new_user)
        db.refresh(new_paciente)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar el paciente: {str(e)}"
        )

    # Generar token de acceso para auto-login
    token = create_access_token(data={"sub": new_user.username, "user_role": "PACIENTE"})

    return {
        "message": "Paciente registrado exitosamente",
        "accessToken": token,
        "user": new_user
    }
