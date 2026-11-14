import re
from datetime import datetime, date, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.models import (
    Usuario,
    UserRoleEnum,
    Paciente,
    Odontologo,
    Personal,
    EspecialidadEnum,
    Cita,
    EstadoCitaEnum,
)
from app.core.security import get_password_hash
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    PerfilUpdateRequest,
)


def _to_usuario_response(u: Usuario) -> UsuarioResponse:
    nombre_completo = None
    correo = None
    telefono = None
    especialidad = None
    colegiatura = None
    descripcion = None

    if getattr(u, "odontologo", None):
        odon = u.odontologo
        nombre_completo = f"{odon.nombres} {odon.apellidos}".strip()
        correo = odon.correo
        telefono = odon.telefono
        colegiatura = odon.colegiatura
        esp_val = odon.especialidad.value if hasattr(odon.especialidad, "value") else str(odon.especialidad)
        especialidad = esp_val
        descripcion = f"Especialista en {esp_val.replace('_', ' ').capitalize()}."
        if colegiatura:
            descripcion = f"Especialista en {esp_val.replace('_', ' ').capitalize()} - Colegiatura {colegiatura}."
    elif getattr(u, "paciente", None):
        pac = u.paciente
        nombre_completo = f"{pac.nombres} {pac.apellidos}".strip()
        correo = pac.correo
        telefono = pac.telefono

    role_val = u.user_role.value if hasattr(u.user_role, "value") else str(u.user_role)

    return UsuarioResponse(
        username=u.username,
        user_role=role_val,
        activo=u.activo,
        fecha_registro=u.fecha_registro,
        nombre_completo=nombre_completo or u.username,
        correo=correo,
        telefono=telefono,
        especialidad=especialidad,
        colegiatura=colegiatura,
        descripcion=descripcion,
        ultimo_acceso=None
    )


def _separar_nombre_completo(nombre_completo: Optional[str], default_username: str) -> Tuple[str, str]:
    if not nombre_completo or not nombre_completo.strip():
        return default_username, ""
    partes = nombre_completo.strip().split()
    if len(partes) == 1:
        return partes[0], ""
    nombres = partes[0]
    apellidos = " ".join(partes[1:])
    return nombres[:100], apellidos[:100]


def _generar_dni_disponible(db: Session, username: str) -> str:
    clean = re.sub(r"\D", "", username)
    if len(clean) == 8:
        existe_pac = db.query(Paciente).filter(Paciente.dni == clean).first()
        existe_per = db.query(Personal).filter(Personal.dni == clean).first()
        if not existe_pac and not existe_per:
            return clean

    base_num = abs(hash(username)) % 80000000 + 10000000
    for offset in range(5000):
        candidato = str(base_num + offset)[:8]
        existe_pac = db.query(Paciente).filter(Paciente.dni == candidato).first()
        existe_per = db.query(Personal).filter(Personal.dni == candidato).first()
        if not existe_pac and not existe_per:
            return candidato

    import random
    while True:
        candidato = str(random.randint(10000000, 99999999))
        existe_pac = db.query(Paciente).filter(Paciente.dni == candidato).first()
        existe_per = db.query(Personal).filter(Personal.dni == candidato).first()
        if not existe_pac and not existe_per:
            return candidato


def _generar_telefono_personal(db: Session, base_tel: Optional[str], username: str) -> str:
    if base_tel and base_tel.strip():
        clean = re.sub(r"\D", "", base_tel.strip())
        if len(clean) == 9:
            if not db.query(Personal).filter(Personal.telefono == clean).first():
                return clean

    base_num = abs(hash(username)) % 80000000 + 10000000
    for offset in range(5000):
        candidato = f"9{str(base_num + offset)[:8]}"
        if not db.query(Personal).filter(Personal.telefono == candidato).first():
            return candidato

    import random
    while True:
        candidato = f"9{random.randint(10000000, 99999999)}"
        if not db.query(Personal).filter(Personal.telefono == candidato).first():
            return candidato


def _generar_correo_personal(db: Session, base_correo: Optional[str], username: str) -> str:
    if base_correo and base_correo.strip():
        clean = base_correo.strip().lower()
        if not db.query(Personal).filter(Personal.correo == clean).first():
            return clean

    cand = f"{username.strip().lower()}@solident.pe"
    if not db.query(Personal).filter(Personal.correo == cand).first():
        return cand

    for i in range(1, 1000):
        cand_i = f"{username.strip().lower()}{i}@solident.pe"
        if not db.query(Personal).filter(Personal.correo == cand_i).first():
            return cand_i

    return f"{username.strip().lower()}@solident.pe"


def _generar_colegiatura_odontologo(db: Session, dni: str) -> str:
    prefijo = f"COP-{dni[:5]}"
    if not db.query(Odontologo).filter(Odontologo.colegiatura == prefijo).first():
        return prefijo
    for i in range(1, 1000):
        cand = f"COP-{dni[:4]}{i}"
        if not db.query(Odontologo).filter(Odontologo.colegiatura == cand).first():
            return cand
    return f"COP-{dni[:5]}"


def _asegurar_perfil_consistente(
    db: Session,
    usuario: Usuario,
    nombre_completo: Optional[str] = None,
    correo: Optional[str] = None,
    telefono: Optional[str] = None,
    especialidad: Optional[str] = None,
    colegiatura: Optional[str] = None,
) -> None:
    """
    Garantiza que el perfil asociado (Paciente u Odontólogo) exista y mantenga
    los datos de contacto sincronizados según el rol del usuario.
    """
    clean_username = usuario.username.strip()

    if usuario.user_role == UserRoleEnum.ODONTOLOGO:
        if not usuario.odontologo:
            dni = _generar_dni_disponible(db, clean_username)
            nombres, apellidos = _separar_nombre_completo(nombre_completo, clean_username)
            if usuario.paciente:
                if not nombre_completo:
                    nombres = usuario.paciente.nombres
                    apellidos = usuario.paciente.apellidos
                if not correo:
                    correo = usuario.paciente.correo
                if not telefono:
                    telefono = usuario.paciente.telefono

            correo_odon = _generar_correo_personal(db, correo, clean_username)
            tel_odon = _generar_telefono_personal(db, telefono, clean_username)
            col_odon = colegiatura or _generar_colegiatura_odontologo(db, dni)

            esp_enum = EspecialidadEnum.ORTODONCIA
            if especialidad:
                try:
                    esp_enum = EspecialidadEnum(especialidad.strip().upper())
                except ValueError:
                    esp_enum = EspecialidadEnum.ORTODONCIA

            nuevo_odon = Odontologo(
                dni=dni,
                username=clean_username,
                nombres=nombres,
                apellidos=apellidos,
                correo=correo_odon,
                telefono=tel_odon,
                activo=usuario.activo,
                fecha_registro=datetime.now(timezone.utc),
                colegiatura=col_odon,
                especialidad=esp_enum,
            )
            db.add(nuevo_odon)
            usuario.odontologo = nuevo_odon
        else:
            if nombre_completo:
                n, a = _separar_nombre_completo(nombre_completo, clean_username)
                usuario.odontologo.nombres = n
                usuario.odontologo.apellidos = a
            if correo is not None and correo.strip():
                clean_c = correo.strip().lower()
                otro = db.query(Personal).filter(Personal.correo == clean_c, Personal.dni != usuario.odontologo.dni).first()
                if not otro:
                    usuario.odontologo.correo = clean_c
            if telefono is not None and telefono.strip():
                clean_t = telefono.strip()
                otro_t = db.query(Personal).filter(Personal.telefono == clean_t, Personal.dni != usuario.odontologo.dni).first()
                if not otro_t:
                    usuario.odontologo.telefono = clean_t
            if especialidad:
                try:
                    usuario.odontologo.especialidad = EspecialidadEnum(especialidad.strip().upper())
                except ValueError:
                    pass
            if colegiatura:
                usuario.odontologo.colegiatura = colegiatura.strip()

    elif usuario.user_role == UserRoleEnum.PACIENTE:
        if not usuario.paciente:
            nombres, apellidos = _separar_nombre_completo(nombre_completo, clean_username)
            if usuario.odontologo:
                if not nombre_completo:
                    nombres = usuario.odontologo.nombres
                    apellidos = usuario.odontologo.apellidos
                if not correo:
                    correo = usuario.odontologo.correo
                if not telefono:
                    telefono = usuario.odontologo.telefono

            dni = _generar_dni_disponible(db, clean_username)
            correo_final = correo.strip().lower() if correo and correo.strip() else None
            if correo_final and db.query(Paciente).filter(Paciente.correo == correo_final).first():
                correo_final = None
            telefono_final = telefono.strip() if telefono and telefono.strip() else None
            if telefono_final and db.query(Paciente).filter(Paciente.telefono == telefono_final).first():
                telefono_final = None

            nuevo_pac = Paciente(
                dni=dni,
                username=clean_username,
                nombres=nombres,
                apellidos=apellidos,
                correo=correo_final,
                telefono=telefono_final,
                direccion=None,
                observaciones="Perfil de Paciente del sistema",
                fecha_nacimiento=date(2000, 1, 1),
                fecha_registro=datetime.now(timezone.utc),
            )
            db.add(nuevo_pac)
            usuario.paciente = nuevo_pac
        else:
            if nombre_completo:
                n, a = _separar_nombre_completo(nombre_completo, clean_username)
                usuario.paciente.nombres = n
                usuario.paciente.apellidos = a
            if correo is not None:
                clean_c = correo.strip().lower() if correo.strip() else None
                if clean_c:
                    otro = db.query(Paciente).filter(Paciente.correo == clean_c, Paciente.dni != usuario.paciente.dni).first()
                    if not otro:
                        usuario.paciente.correo = clean_c
                else:
                    usuario.paciente.correo = None
            if telefono is not None:
                clean_t = telefono.strip() if telefono.strip() else None
                if clean_t:
                    otro_t = db.query(Paciente).filter(Paciente.telefono == clean_t, Paciente.dni != usuario.paciente.dni).first()
                    if not otro_t:
                        usuario.paciente.telefono = clean_t
                else:
                    usuario.paciente.telefono = None

    elif usuario.user_role == UserRoleEnum.SYSTEM_ADMIN:
        # Para administradores, si no tienen perfil asociado, se utiliza una ficha de Paciente
        # como contenedor de identidad (nombres, correo, teléfono) sin exponerse en la lista médica.
        if not usuario.paciente and not usuario.odontologo:
            nombres, apellidos = _separar_nombre_completo(nombre_completo, clean_username)
            dni = _generar_dni_disponible(db, clean_username)
            correo_final = correo.strip().lower() if correo and correo.strip() else None
            if correo_final and db.query(Paciente).filter(Paciente.correo == correo_final).first():
                correo_final = None
            telefono_final = telefono.strip() if telefono and telefono.strip() else None
            if telefono_final and db.query(Paciente).filter(Paciente.telefono == telefono_final).first():
                telefono_final = None

            admin_pac = Paciente(
                dni=dni,
                username=clean_username,
                nombres=nombres,
                apellidos=apellidos,
                correo=correo_final,
                telefono=telefono_final,
                direccion=None,
                observaciones="Perfil de Administrador del Sistema",
                fecha_nacimiento=date(2000, 1, 1),
                fecha_registro=datetime.now(timezone.utc),
            )
            db.add(admin_pac)
            usuario.paciente = admin_pac
        else:
            target = usuario.paciente or usuario.odontologo
            if target:
                if nombre_completo:
                    n, a = _separar_nombre_completo(nombre_completo, clean_username)
                    target.nombres = n
                    target.apellidos = a
                if correo is not None:
                    target.correo = correo.strip().lower() if correo.strip() else None
                if telefono is not None:
                    target.telefono = telefono.strip() if telefono.strip() else None


def obtener_perfil_me(db: Session, current_user: Usuario) -> UsuarioResponse:
    """
    Retorna la ficha y datos personales del usuario conectado actualmente (me).
    No requiere permisos de administrador.
    """
    usuario = (
        db.query(Usuario)
        .options(
            joinedload(Usuario.odontologo),
            joinedload(Usuario.paciente)
        )
        .filter(Usuario.username == current_user.username)
        .first()
    )
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en la base de datos."
        )

    if not usuario.odontologo and not usuario.paciente:
        _asegurar_perfil_consistente(db, usuario)
        try:
            db.commit()
            db.refresh(usuario)
        except Exception:
            db.rollback()

    return _to_usuario_response(usuario)


def actualizar_perfil_me(db: Session, data: PerfilUpdateRequest, current_user: Usuario) -> UsuarioResponse:
    """
    Permite a cualquier usuario autenticado actualizar sus propios datos personales
    y de contacto (y especialidad si es odontólogo). No permite cambiar rol ni estado activo.
    """
    usuario = (
        db.query(Usuario)
        .options(
            joinedload(Usuario.odontologo),
            joinedload(Usuario.paciente)
        )
        .filter(Usuario.username == current_user.username)
        .first()
    )
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en la base de datos."
        )

    clean_correo = data.correo.strip().lower() if data.correo and data.correo.strip() else None
    clean_tel = data.telefono.strip() if data.telefono and data.telefono.strip() else None

    # Validar duplicados de correo en la base de datos
    if clean_correo:
        if usuario.paciente:
            otro_p = db.query(Paciente).filter(Paciente.correo == clean_correo, Paciente.dni != usuario.paciente.dni).first()
            if otro_p:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El correo electrónico ya se encuentra registrado por otro usuario."
                )
        if usuario.odontologo:
            otro_per = db.query(Personal).filter(Personal.correo == clean_correo, Personal.dni != usuario.odontologo.dni).first()
            if otro_per:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El correo electrónico ya se encuentra registrado por otro especialista."
                )

    # Validar duplicados de teléfono en la base de datos
    if clean_tel:
        if usuario.paciente:
            otro_tp = db.query(Paciente).filter(Paciente.telefono == clean_tel, Paciente.dni != usuario.paciente.dni).first()
            if otro_tp:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El número de teléfono ya se encuentra registrado por otro usuario."
                )
        if usuario.odontologo:
            otro_tper = db.query(Personal).filter(Personal.telefono == clean_tel, Personal.dni != usuario.odontologo.dni).first()
            if otro_tper:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El número de teléfono ya se encuentra registrado por otro especialista."
                )

    # Actualizar según el tipo de perfil existente
    if usuario.user_role == UserRoleEnum.ODONTOLOGO:
        if not usuario.odontologo:
            _asegurar_perfil_consistente(
                db=db,
                usuario=usuario,
                nombre_completo=data.nombre_completo,
                correo=clean_correo,
                telefono=clean_tel,
                especialidad=data.especialidad,
            )
        else:
            if data.nombre_completo:
                n, a = _separar_nombre_completo(data.nombre_completo, usuario.username)
                usuario.odontologo.nombres = n
                usuario.odontologo.apellidos = a
            if clean_correo:
                usuario.odontologo.correo = clean_correo
            if clean_tel:
                usuario.odontologo.telefono = clean_tel
            if data.especialidad:
                clean_esp = data.especialidad.strip().upper()
                try:
                    usuario.odontologo.especialidad = EspecialidadEnum(clean_esp)
                except ValueError:
                    matched = False
                    for e in EspecialidadEnum:
                        if e.value.replace("_", " ").lower() == clean_esp.replace("_", " ").lower():
                            usuario.odontologo.especialidad = e
                            matched = True
                            break
                    if not matched:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Especialidad '{data.especialidad}' no es válida."
                        )
    else:
        # Rol PACIENTE o SYSTEM_ADMIN
        if not usuario.paciente:
            _asegurar_perfil_consistente(
                db=db,
                usuario=usuario,
                nombre_completo=data.nombre_completo,
                correo=clean_correo,
                telefono=clean_tel,
            )
        else:
            if data.nombre_completo:
                n, a = _separar_nombre_completo(data.nombre_completo, usuario.username)
                usuario.paciente.nombres = n
                usuario.paciente.apellidos = a
            if data.correo is not None:
                usuario.paciente.correo = clean_correo
            if data.telefono is not None:
                usuario.paciente.telefono = clean_tel

    db.commit()
    db.refresh(usuario)
    return _to_usuario_response(usuario)


def listar_usuarios(db: Session, current_user: Usuario) -> List[UsuarioResponse]:
    """Lista todos los usuarios del sistema (Solo administradores)."""
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )

    usuarios = (
        db.query(Usuario)
        .options(
            joinedload(Usuario.odontologo),
            joinedload(Usuario.paciente)
        )
        .order_by(Usuario.fecha_registro.desc())
        .all()
    )

    # Auto-sanación de usuarios creados sin perfil asociado para que siempre devuelvan datos de contacto
    hubo_cambios = False
    for u in usuarios:
        if not u.odontologo and not u.paciente:
            _asegurar_perfil_consistente(db, u)
            hubo_cambios = True

    if hubo_cambios:
        try:
            db.commit()
        except Exception:
            db.rollback()

    return [_to_usuario_response(u) for u in usuarios]


def obtener_usuario(db: Session, username: str, current_user: Usuario) -> UsuarioResponse:
    """Obtiene el detalle de un usuario por su username (Solo admin o propio usuario)."""
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN") and current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )

    usuario = (
        db.query(Usuario)
        .options(
            joinedload(Usuario.odontologo),
            joinedload(Usuario.paciente)
        )
        .filter(Usuario.username == username)
        .first()
    )
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario '{username}' no encontrado."
        )

    if not usuario.odontologo and not usuario.paciente:
        _asegurar_perfil_consistente(db, usuario)
        try:
            db.commit()
            db.refresh(usuario)
        except Exception:
            db.rollback()

    return _to_usuario_response(usuario)


def crear_usuario(db: Session, data: UsuarioCreate, current_user: Usuario) -> UsuarioResponse:
    """Crea un nuevo usuario en la base de datos asegurando sus datos de contacto y perfil."""
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )

    clean_username = data.username.strip()
    existente = db.query(Usuario).filter(Usuario.username == clean_username).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El nombre de usuario '{clean_username}' ya existe en el sistema."
        )

    clean_rol = data.user_role.strip().upper()
    if clean_rol == "ADMIN":
        clean_rol = "SYSTEM_ADMIN"
    try:
        role_enum = UserRoleEnum(clean_rol)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol '{data.user_role}' no es válido."
        )

    hashed_pw = get_password_hash(data.password)
    nuevo_usuario = Usuario(
        username=clean_username,
        password=hashed_pw,
        activo=data.activo,
        user_role=role_enum,
        fecha_registro=datetime.now(timezone.utc),
    )
    db.add(nuevo_usuario)

    _asegurar_perfil_consistente(
        db=db,
        usuario=nuevo_usuario,
        nombre_completo=data.nombre_completo,
        correo=data.correo,
        telefono=data.telefono,
    )

    db.commit()
    db.refresh(nuevo_usuario)

    return _to_usuario_response(nuevo_usuario)


def cambiar_rol_usuario(
    db: Session,
    username: str,
    nuevo_rol_str: str,
    current_user: Usuario,
    especialidad: Optional[str] = None,
    colegiatura: Optional[str] = None
) -> UsuarioResponse:
    """
    Cambia el rol de un usuario y sincroniza de forma consistente
    su perfil y relaciones en la base de datos (Solo Administradores).
    """
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )

    clean_rol = nuevo_rol_str.strip().upper()
    if clean_rol == "ADMIN":
        clean_rol = "SYSTEM_ADMIN"
    try:
        nuevo_rol = UserRoleEnum(clean_rol)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol '{nuevo_rol_str}' no es válido. Debe ser SYSTEM_ADMIN, ODONTOLOGO o PACIENTE."
        )

    if username.strip().lower() == current_user.username.strip().lower() and nuevo_rol != UserRoleEnum.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes quitarte el rol de Administrador a ti mismo en sesión activa."
        )

    usuario = (
        db.query(Usuario)
        .options(
            joinedload(Usuario.odontologo),
            joinedload(Usuario.paciente)
        )
        .filter(Usuario.username == username)
        .first()
    )
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario '{username}' no encontrado."
        )

    usuario.user_role = nuevo_rol

    _asegurar_perfil_consistente(
        db=db,
        usuario=usuario,
        especialidad=especialidad,
        colegiatura=colegiatura
    )

    db.commit()
    db.refresh(usuario)
    return _to_usuario_response(usuario)


def actualizar_usuario(db: Session, username: str, data: UsuarioUpdate, current_user: Usuario) -> UsuarioResponse:
    """Actualiza datos y rol de un usuario existente manteniendo consistencia en sus relaciones."""
    usuario = (
        db.query(Usuario)
        .options(
            joinedload(Usuario.odontologo),
            joinedload(Usuario.paciente)
        )
        .filter(Usuario.username == username)
        .first()
    )
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario '{username}' no encontrado."
        )

    # Si se intenta cambiar de rol, verificar permisos de administrador
    if data.user_role is not None:
        role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
        if role_val not in ("SYSTEM_ADMIN", "ADMIN"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para modificar el rol de usuarios"
            )

        clean_rol = data.user_role.strip().upper()
        if clean_rol == "ADMIN":
            clean_rol = "SYSTEM_ADMIN"
        try:
            nuevo_rol = UserRoleEnum(clean_rol)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol '{data.user_role}' no es válido."
            )

        if username.strip().lower() == current_user.username.strip().lower() and nuevo_rol != UserRoleEnum.SYSTEM_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes quitarte el rol de Administrador a ti mismo en sesión activa."
            )

        usuario.user_role = nuevo_rol

    if data.activo is not None:
        usuario.activo = data.activo
        if usuario.odontologo:
            usuario.odontologo.activo = data.activo

    if data.password:
        usuario.password = get_password_hash(data.password)

    _asegurar_perfil_consistente(
        db=db,
        usuario=usuario,
        nombre_completo=data.nombre_completo,
        correo=data.correo,
        telefono=data.telefono,
    )

    db.commit()
    db.refresh(usuario)

    return _to_usuario_response(usuario)


def toggle_status_usuario(db: Session, username: str, current_user: Usuario) -> UsuarioResponse:
    """Alterna el estado activo de un usuario."""
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )

    usuario = (
        db.query(Usuario)
        .options(
            joinedload(Usuario.odontologo),
            joinedload(Usuario.paciente)
        )
        .filter(Usuario.username == username)
        .first()
    )
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario '{username}' no encontrado."
        )

    usuario.activo = not usuario.activo
    if usuario.odontologo:
        usuario.odontologo.activo = usuario.activo

    db.commit()
    db.refresh(usuario)

    return _to_usuario_response(usuario)


def eliminar_usuario(db: Session, username: str, current_user: Usuario) -> dict:
    """
    Elimina definitivamente un usuario del sistema (Solo Administradores).
    Impide auto-eliminación y valida citas médicas activas.
    """
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )

    if username.strip().lower() == current_user.username.strip().lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propia cuenta de administrador en sesión activa."
        )

    usuario = (
        db.query(Usuario)
        .options(
            joinedload(Usuario.odontologo),
            joinedload(Usuario.paciente)
        )
        .filter(Usuario.username == username)
        .first()
    )
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario '{username}' no encontrado."
        )

    # Validar citas activas para no dejar inconsistencias clínicas
    estados_activos = [
        EstadoCitaEnum.PROGRAMADA,
        EstadoCitaEnum.CONFIRMADA,
        EstadoCitaEnum.REPROGRAMADA,
        EstadoCitaEnum.EN_PROCESO,
    ]

    if usuario.paciente:
        citas_activas_pac = (
            db.query(Cita)
            .filter(
                Cita.dni_paciente == usuario.paciente.dni,
                Cita.estado.in_(estados_activos)
            )
            .count()
        )
        if citas_activas_pac > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede eliminar el usuario porque tiene {citas_activas_pac} cita(s) médica(s) activa(s) o programada(s). Debes cancelarlas o reprogramarlas primero."
            )

    if usuario.odontologo:
        citas_activas_odon = (
            db.query(Cita)
            .filter(
                Cita.dni_odontologo == usuario.odontologo.dni,
                Cita.estado.in_(estados_activos)
            )
            .count()
        )
        if citas_activas_odon > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede eliminar al especialista porque tiene {citas_activas_odon} cita(s) asignada(s) pendientes de atención. Debes reasignar sus citas primero."
            )

    # Eliminar perfiles asociados y usuario
    if usuario.odontologo:
        db.delete(usuario.odontologo)
    if usuario.paciente:
        db.delete(usuario.paciente)

    db.delete(usuario)
    db.commit()
    return {"message": f"Usuario '{username}' eliminado exitosamente del sistema."}


def listar_odontologos_activos(db: Session) -> List[dict]:
    """
    Obtiene únicamente los usuarios con rol 'ODONTOLOGO' y estado activo (activo=True),
    consultando directamente la fuente de datos donde se gestionan los usuarios del sistema.
    Público: No requiere autenticación.
    """
    usuarios = (
        db.query(Usuario)
        .options(joinedload(Usuario.odontologo))
        .filter(
            Usuario.user_role == UserRoleEnum.ODONTOLOGO,
            Usuario.activo == True
        )
        .order_by(Usuario.username.asc())
        .all()
    )

    resultado = []
    for u in usuarios:
        odon = u.odontologo
        dni = odon.dni if odon else u.username
        nombres = odon.nombres if odon else u.username
        apellidos = odon.apellidos if odon else ""
        nombre_completo = f"{nombres} {apellidos}".strip()

        esp = "Odontología General"
        if odon and odon.especialidad:
            esp = odon.especialidad.value if hasattr(odon.especialidad, "value") else str(odon.especialidad)

        colegiatura = odon.colegiatura if odon else None
        desc = f"Especialista en {esp.replace('_', ' ').capitalize()}."
        if colegiatura:
            desc = f"Especialista en {esp.replace('_', ' ').capitalize()} - Colegiatura {colegiatura}."

        resultado.append({
            "id": dni,
            "dni": dni,
            "username": u.username,
            "nombre": nombre_completo,
            "nombres": nombres,
            "apellidos": apellidos,
            "especialidad": esp,
            "colegiatura": colegiatura,
            "correo": odon.correo if odon else None,
            "telefono": odon.telefono if odon else None,
            "descripcion": desc,
            "activo": u.activo,
        })

    return resultado
