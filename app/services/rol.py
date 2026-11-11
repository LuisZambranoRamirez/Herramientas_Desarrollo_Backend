from typing import Dict, List, Optional, Union
from fastapi import HTTPException, status
from sqlalchemy.exc import DataError, IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.models import PermisosEnum, RolePermisos, UserRoleEnum
from app.schemas.rol import (
    RolePermisoCreate,
    RolePermisoUpdate,
    RoleResponse,
    normalizar_permiso_str,
    normalizar_role_str,
)

_ROLE_METADATA: Dict[UserRoleEnum, Dict[str, object]] = {
    UserRoleEnum.SYSTEM_ADMIN: {
        "descripcion": (
            "Acceso administrativo total. Permite configurar la plataforma, gestionar usuarios, "
            "administrar roles y permisos, auditar pagos y supervisar la operación global de la clínica."
        ),
        "modulos": ["usuarios", "roles", "inventario", "proveedores", "pagos", "citas", "tratamientos"],
    },
    UserRoleEnum.ODONTOLOGO: {
        "descripcion": (
            "Perfil médico clínico. Permite visualizar la agenda de citas médicas, "
            "atender pacientes, registrar evoluciones y tratamientos, y consultar insumos."
        ),
        "modulos": ["agenda", "citas", "pacientes", "tratamientos", "insumos"],
    },
    UserRoleEnum.PACIENTE: {
        "descripcion": (
            "Perfil de usuario final. Permite reservar y consultar sus citas odontológicas, "
            "revisar su historial de tratamientos y verificar comprobantes de pago."
        ),
        "modulos": ["citas", "tratamientos", "pagos"],
    },
}


def _parse_role_enum(role_name: str, *, not_found_on_error: bool = False) -> UserRoleEnum:
    """Convierte un nombre de rol a UserRoleEnum o lanza HTTPException 404/400."""
    try:
        normalized = normalizar_role_str(role_name)
        return UserRoleEnum(normalized)
    except ValueError as exc:
        if not_found_on_error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rol '{role_name}' no encontrado. {str(exc)}",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


def _parse_permiso_enum(permiso_val: str) -> PermisosEnum:
    """Convierte un permiso a PermisosEnum o lanza HTTPException 400."""
    try:
        normalized = normalizar_permiso_str(permiso_val)
        return PermisosEnum(normalized)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


def _build_role_response(
    role_enum: UserRoleEnum,
    registro: Optional[RolePermisos] = None,
) -> RoleResponse:
    """Construye la respuesta serializable de un rol combinando metadatos y tabla role_permisos."""
    meta = _ROLE_METADATA.get(role_enum, {"descripcion": "Rol del sistema.", "modulos": []})
    permiso_val = (
        registro.permisos.value
        if registro is not None and hasattr(registro.permisos, "value")
        else (str(registro.permisos) if registro is not None else None)
    )
    return RoleResponse(
        role=role_enum.value,
        descripcion=str(meta["descripcion"]),
        permisos=permiso_val,
        modulos=list(meta["modulos"]),  # type: ignore[arg-type]
        configurado=registro is not None,
    )


def obtener_roles(db: Session) -> List[RoleResponse]:
    """Lista todos los roles del sistema y sus permisos configurados en role_permisos."""
    registros = db.query(RolePermisos).all()
    registros_por_rol: Dict[UserRoleEnum, RolePermisos] = {r.role: r for r in registros}
    return [
        _build_role_response(role_enum, registros_por_rol.get(role_enum))
        for role_enum in UserRoleEnum
    ]


def obtener_permisos_por_rol(db: Session, role_name: str) -> RoleResponse:
    """Consulta la configuración específica de un rol por su nombre."""
    role_enum = _parse_role_enum(role_name, not_found_on_error=True)
    registro = db.query(RolePermisos).filter(RolePermisos.role == role_enum).first()
    return _build_role_response(role_enum, registro)


def guardar_o_actualizar_permisos_rol(
    db: Session,
    role_name: str,
    data: Union[RolePermisoCreate, RolePermisoUpdate],
    *,
    not_found_on_unknown_role: bool = False,
) -> RoleResponse:
    """Crea la entrada en role_permisos si no existe o actualiza sus permisos de forma transaccional."""
    role_enum = _parse_role_enum(role_name, not_found_on_error=not_found_on_unknown_role)
    permiso_enum = _parse_permiso_enum(data.permisos)

    registro = db.query(RolePermisos).filter(RolePermisos.role == role_enum).first()
    if registro is None:
        registro = RolePermisos(role=role_enum, permisos=permiso_enum)
        db.add(registro)
    else:
        registro.permisos = permiso_enum

    try:
        db.commit()
        db.refresh(registro)
    except (DataError, IntegrityError) as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Datos inválidos al persistir permisos para el rol '{role_enum.value}': {str(exc.orig)}",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno de base de datos al guardar los permisos del rol.",
        )

    return _build_role_response(role_enum, registro)
