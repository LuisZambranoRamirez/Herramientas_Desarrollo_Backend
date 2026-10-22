from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Usuario, Paciente, UserRoleEnum
from app.schemas.auth import LoginRequest, RegistroPaciente
from app.core.security import verify_password, get_password_hash, create_access_token

def iniciar_sesion(db: Session, credentials: LoginRequest) -> dict:
    """Valida las credenciales y genera el token de acceso del usuario."""
    user = db.query(Usuario).filter(Usuario.username == credentials.username).first()

        # Verificar si existe el usuario
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario no existe.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar si la contraseña es correcta
    if not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La contraseña es incorrecta.",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
    if db.query(Usuario).filter(Usuario.username == data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya se encuentra registrado"
        )

    if db.query(Paciente).filter(Paciente.dni == data.dni).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El DNI ya se encuentra registrado"
        )

    if db.query(Paciente).filter(Paciente.correo == data.correo).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya se encuentra registrado"
        )

    if data.telefono and db.query(Paciente).filter(Paciente.telefono == data.telefono).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de teléfono ya se encuentra registrado"
        )

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

    now = datetime.now(timezone.utc)

    new_user = Usuario(
        username=data.username,
        password=get_password_hash(data.password),
        activo=True,
        user_role=UserRoleEnum.PACIENTE,
        fecha_registro=now
    )

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
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al registrar el paciente."
        )

    token = create_access_token(data={"sub": new_user.username, "user_role": "PACIENTE"})

    return {
        "message": "Paciente registrado exitosamente",
        "accessToken": token,
        "user": new_user
    }