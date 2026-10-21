from datetime import datetime, date, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.models import (
    Usuario,
    Cita,
    EstadoCitaEnum,
    Paciente,
    Odontologo,
)
from app.schemas.cita import CitaCreate, CitaEstadoUpdate, CitaUpdate


def format_cita_response(cita: Cita) -> dict:
    """Transforma un modelo Cita a diccionario con datos de relaciones."""
    paciente_data = None
    if cita.paciente:
        paciente_data = {
            "dni": cita.paciente.dni,
            "nombres": cita.paciente.nombres,
            "apellidos": cita.paciente.apellidos,
            "telefono": cita.paciente.telefono,
            "correo": cita.paciente.correo,
        }

    odontologo_data = None
    if cita.odontologo:
        esp = (
            cita.odontologo.especialidad.value
            if hasattr(cita.odontologo.especialidad, "value")
            else str(cita.odontologo.especialidad)
        )
        odontologo_data = {
            "dni": cita.odontologo.dni,
            "nombres": nombres,
            "apellidos": apellidos,
            "especialidad": esp,
            "colegiatura": cita.odontologo.colegiatura,
        }

    return {
        "cita_id": str(cita.cita_id),
        "dni_paciente": cita.dni_paciente,
        "dni_odontologo": cita.dni_odontologo,
        "fecha": cita.fecha,
        "hora": cita.hora,
        "motivo_consulta": cita.motivo_consulta,
        "diagnostico": cita.diagnostico,
        "estado": (
            cita.estado.value if hasattr(cita.estado, "value") else str(cita.estado)
        ),
        "fecha_registro": cita.fecha_registro,
        "paciente": paciente_data,
        "odontologo": odontologo_data,
    }


def _query_citas_con_relaciones(db: Session):
    """Consulta base de citas con paciente y odontólogo precargados."""
    return db.query(Cita).options(
        joinedload(Cita.paciente),
        joinedload(Cita.odontologo),
    )


def listar_odontologos_disponibles(db: Session) -> List[dict]:
    odontologos = (
        db.query(Odontologo)
        .filter(Odontologo.activo == True)  # noqa: E712
        .order_by(Odontologo.apellidos.asc(), Odontologo.nombres.asc())
        .all()
    )
    resultado = []
    for o in odontologos:
        esp = o.especialidad.value if hasattr(o.especialidad, "value") else str(o.especialidad)
        resultado.append(
            {
                "dni": o.dni,
                "nombres": o.nombres,
                "apellidos": o.apellidos,
                "especialidad": esp,
                "colegiatura": o.colegiatura,
            }
        )
    return resultado


def agendar_cita(db: Session, data: CitaCreate, current_user: Usuario) -> dict:
    # 1. Determinar DNI del paciente
    if current_user.user_role == "PACIENTE":
        paciente = (
            db.query(Paciente)
            .filter(Paciente.username == current_user.username)
            .first()
        )
        if not paciente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró el registro de paciente asociado a este usuario",
            )
        dni_paciente = paciente.dni
    else:
        if not data.dni_paciente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se debe proporcionar el DNI del paciente",
            )
        paciente = db.query(Paciente).filter(Paciente.dni == data.dni_paciente).first()
        if not paciente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe ningún paciente con DNI {data.dni_paciente}",
            )
        dni_paciente = data.dni_paciente

    # 2. Validar que el odontólogo exista
    odontologo = (
        db.query(Odontologo).filter(Odontologo.dni == data.dni_odontologo).first()
    )
    if not odontologo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El odontólogo seleccionado no existe",
        )

    # 3. Validar disponibilidad de horario (evitar doble cita al mismo odontólogo)
    # ✅ CORREGIDO: usar miembros del Enum, no strings
    conflicto = (
        db.query(Cita)
        .filter(
            Cita.dni_odontologo == data.dni_odontologo,
            Cita.fecha == data.fecha,
            Cita.hora == data.hora,
            Cita.estado.notin_(
                [EstadoCitaEnum.CANCELADA, EstadoCitaEnum.NO_ASISTIO]
            ),
        )
        .first()
    )
    if conflicto:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El odontólogo ya tiene una cita programada para esa fecha y hora",
        )

    # 4. Crear la cita
    # ✅ CORREGIDO: pasar el Enum directamente, no .value
    nueva_cita = Cita(
        dni_paciente=dni_paciente,
        dni_odontologo=data.dni_odontologo,
        fecha=data.fecha,
        hora=data.hora,
        motivo_consulta=data.motivo_consulta,
        diagnostico=(data.diagnostico or None),
        estado=EstadoCitaEnum.PROGRAMADA,
        fecha_registro=datetime.utcnow(),
    )

    db.add(nueva_cita)
    db.commit()
    db.refresh(nueva_cita)

    # ✅ Recargar con relaciones para que format_cita_response traiga paciente/odontologo
    nueva_cita = (
        _query_citas_con_relaciones(db)
        .filter(Cita.cita_id == nueva_cita.cita_id)
        .first()
    )

    return format_cita_response(nueva_cita)


def listar_mis_citas(db: Session, current_user: Usuario) -> List[dict]:
    query = _query_citas_con_relaciones(db)

    if current_user.user_role == "PACIENTE":
        paciente = (
            db.query(Paciente)
            .filter(Paciente.username == current_user.username)
            .first()
        )
        if not paciente:
            return []
        citas = (
            query.filter(Cita.dni_paciente == paciente.dni)
            .order_by(Cita.fecha.desc(), Cita.hora.desc())
            .all()
        )
    elif current_user.user_role == "ODONTOLOGO":
        odontologo = (
            db.query(Odontologo)
            .filter(Odontologo.username == current_user.username)
            .first()
        )
        if not odontologo:
            return []
        citas = (
            query.filter(Cita.dni_odontologo == odontologo.dni)
            .order_by(Cita.fecha.desc(), Cita.hora.desc())
            .all()
        )
    else:
        citas = query.order_by(Cita.fecha.desc(), Cita.hora.desc()).all()

    return [format_cita_response(c) for c in citas]


def listar_citas(
    db: Session,
    current_user: Usuario,
    fecha: Optional[date] = None,
    estado: Optional[str] = None,
    dni_paciente: Optional[str] = None,
    dni_odontologo: Optional[str] = None,
) -> List[dict]:
    query = _query_citas_con_relaciones(db)

    if current_user.user_role == "PACIENTE":
        paciente = (
            db.query(Paciente)
            .filter(Paciente.username == current_user.username)
            .first()
        )
        if not paciente:
            return []
        query = query.filter(Cita.dni_paciente == paciente.dni)
    else:
        if dni_paciente:
            query = query.filter(Cita.dni_paciente == dni_paciente)
        if dni_odontologo:
            query = query.filter(Cita.dni_odontologo == dni_odontologo)

    if fecha:
        query = query.filter(Cita.fecha == fecha)
    if estado:
        # ✅ CORREGIDO: comparar con Enum
        try:
            estado_enum = EstadoCitaEnum(estado.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado inválido. Opciones: {[e.value for e in EstadoCitaEnum]}",
            )
        query = query.filter(Cita.estado == estado_enum)

    citas = query.order_by(Cita.fecha.desc(), Cita.hora.desc()).all()
    return [format_cita_response(c) for c in citas]


def obtener_detalle_cita(db: Session, cita_id: str, current_user: Usuario) -> dict:
    cita = (
        _query_citas_con_relaciones(db).filter(Cita.cita_id == cita_id).first()
    )
    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada"
        )

    if current_user.user_role == "PACIENTE":
        paciente = (
            db.query(Paciente)
            .filter(Paciente.username == current_user.username)
            .first()
        )
        if not paciente or cita.dni_paciente != paciente.dni:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver esta cita",
            )

    return format_cita_response(cita)


def actualizar_estado_cita(
    db: Session, cita_id: str, data: CitaEstadoUpdate, current_user: Usuario
) -> dict:
    cita = db.query(Cita).filter(Cita.cita_id == cita_id).first()
    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada"
        )

    if current_user.user_role == "PACIENTE":
        paciente = (
            db.query(Paciente)
            .filter(Paciente.username == current_user.username)
            .first()
        )
        if not paciente or cita.dni_paciente != paciente.dni:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para modificar esta cita",
            )
        # ✅ CORREGIDO: comparar con Enum
        if data.estado.upper() != EstadoCitaEnum.CANCELADA.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los pacientes solo pueden cancelar sus citas",
            )

    # ✅ CORREGIDO: convertir a Enum, no usar strings
    try:
        estado_enum = EstadoCitaEnum(data.estado.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estado inválido. Opciones permitidas: {[e.value for e in EstadoCitaEnum]}",
        )

    cita.estado = estado_enum
    if data.diagnostico:
        cita.diagnostico = data.diagnostico

    db.commit()
    db.refresh(cita)

    cita = (
        _query_citas_con_relaciones(db).filter(Cita.cita_id == cita_id).first()
    )
    return format_cita_response(cita)


def cancelar_cita(db: Session, cita_id: str, current_user: Usuario) -> dict:
    cita = db.query(Cita).filter(Cita.cita_id == cita_id).first()
    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada"
        )

    if current_user.user_role == "PACIENTE":
        paciente = (
            db.query(Paciente)
            .filter(Paciente.username == current_user.username)
            .first()
        )
        if not paciente or cita.dni_paciente != paciente.dni:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para cancelar esta cita",
            )

    # ✅ CORREGIDO: asignar Enum, no .value
    cita.estado = EstadoCitaEnum.CANCELADA
    db.commit()
    db.refresh(cita)

    cita = (
        _query_citas_con_relaciones(db).filter(Cita.cita_id == cita_id).first()
    )
    return format_cita_response(cita)


def actualizar_cita(
    db: Session, cita_id: str, data: CitaUpdate, current_user: Usuario
) -> dict:
    """Edita / reprograma una cita. Solo personal (administrador u odontólogo)."""
    if current_user.user_role == "PACIENTE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los pacientes no pueden modificar citas; solo cancelarlas",
        )

    cita = db.query(Cita).filter(Cita.cita_id == cita_id).first()
    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada"
        )

    nuevo_odontologo = data.dni_odontologo or cita.dni_odontologo
    nueva_fecha = data.fecha or cita.fecha
    nueva_hora = data.hora if data.hora is not None else cita.hora

    if data.dni_odontologo and not db.query(Odontologo).filter(
        Odontologo.dni == data.dni_odontologo
    ).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El odontólogo seleccionado no existe",
        )

    # ✅ CORREGIDO: manejar Enum correctamente
    if data.estado:
        try:
            estado_final = EstadoCitaEnum(data.estado.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado inválido. Opciones permitidas: {[e.value for e in EstadoCitaEnum]}",
            )
    else:
        estado_final = cita.estado

    # Evitar doble cita del odontólogo en la misma fecha/hora (excluye esta cita)
    # ✅ CORREGIDO: usar Enum, no strings
    if estado_final not in (EstadoCitaEnum.CANCELADA, EstadoCitaEnum.NO_ASISTIO):
        conflicto = (
            db.query(Cita)
            .filter(
                Cita.cita_id != cita.cita_id,
                Cita.dni_odontologo == nuevo_odontologo,
                Cita.fecha == nueva_fecha,
                Cita.hora == nueva_hora,
                Cita.estado.notin_(
                    [EstadoCitaEnum.CANCELADA, EstadoCitaEnum.NO_ASISTIO]
                ),
            )
            .first()
        )
        if conflicto:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El odontólogo ya tiene una cita programada para esa fecha y hora",
            )

    cita.dni_odontologo = nuevo_odontologo
    cita.fecha = nueva_fecha
    cita.hora = nueva_hora
    cita.estado = estado_final
    if data.motivo_consulta is not None:
        cita.motivo_consulta = data.motivo_consulta
    if data.diagnostico is not None:
        cita.diagnostico = data.diagnostico or None

    db.commit()
    db.expire_all()
    cita = (
        _query_citas_con_relaciones(db).filter(Cita.cita_id == cita_id).first()
    )
    return format_cita_response(cita)
