import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import (
    TratamientoPaciente,
    AgendaTratamientos,
    TratamientoOdontologicoEnum,
    EstadoTratamientoEnum,
    DiaSemanaEnum,
    Usuario,
    Paciente,
    Odontologo
)
from app.schemas.tratamiento import (
    TratamientoCreate,
    TratamientoUpdate,
    AgendaTratamientoCreate
)

def listar_tratamientos(
    db: Session,
    current_user: Usuario,
    paciente_dni: Optional[str] = None,
    estado: Optional[str] = None
) -> List[TratamientoPaciente]:
    query = db.query(TratamientoPaciente)

    role_val = current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)
    if role_val == "PACIENTE":
        pac = db.query(Paciente).filter(Paciente.username == current_user.username).first()
        if not pac:
            return []
        query = query.filter(TratamientoPaciente.dni_paciente == pac.dni)
    elif role_val == "ODONTOLOGO":
        odont = db.query(Odontologo).filter(Odontologo.username == current_user.username).first()
        if not odont:
            return []
        query = query.filter(TratamientoPaciente.dni_odontologo == odont.dni)
    elif paciente_dni:
        query = query.filter(TratamientoPaciente.dni_paciente == paciente_dni)

    if estado:
        query = query.filter(TratamientoPaciente.estado == estado)

    return query.order_by(TratamientoPaciente.fecha_registro.desc()).all()

def obtener_tratamiento_por_id(db: Session, tratamiento_id: uuid.UUID, current_user: Usuario) -> TratamientoPaciente:
    trat = db.query(TratamientoPaciente).filter(TratamientoPaciente.tratamiento_paciente_id == tratamiento_id).first()
    if not trat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tratamiento no encontrado."
        )

    role_val = current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)
    if role_val == "PACIENTE":
        pac = db.query(Paciente).filter(Paciente.username == current_user.username).first()
        if not pac or pac.dni != trat.dni_paciente:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver este tratamiento."
            )
    return trat

def crear_tratamiento(db: Session, data: TratamientoCreate, current_user: Usuario) -> TratamientoPaciente:
    role_val = current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)
    if role_val not in ("SYSTEM_ADMIN", "ODONTOLOGO"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores u odontólogos pueden crear tratamientos."
        )

    pac = db.query(Paciente).filter(Paciente.dni == data.dni_paciente).first()
    if not pac:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El paciente con DNI {data.dni_paciente} no existe."
        )

    odont = db.query(Odontologo).filter(Odontologo.dni == data.dni_odontologo).first()
    if not odont:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El odontólogo con DNI {data.dni_odontologo} no existe."
        )

    nuevo_trat = TratamientoPaciente(
        dni_paciente=data.dni_paciente,
        dni_odontologo=data.dni_odontologo,
        observaciones=data.observaciones,
        precio=data.precio,
        tratamiento=data.tratamiento,
        estado=data.estado or EstadoTratamientoEnum.INICIADO.value,
        fecha_registro=datetime.now(timezone.utc)
    )

    try:
        db.add(nuevo_trat)
        db.commit()
        db.refresh(nuevo_trat)
        return nuevo_trat
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al registrar el tratamiento."
        )

def actualizar_tratamiento(db: Session, tratamiento_id: uuid.UUID, data: TratamientoUpdate, current_user: Usuario) -> TratamientoPaciente:
    trat = obtener_tratamiento_por_id(db, tratamiento_id, current_user)

    role_val = current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)
    if role_val not in ("SYSTEM_ADMIN", "ODONTOLOGO"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores u odontólogos pueden modificar tratamientos."
        )

    if data.observaciones is not None:
        trat.observaciones = data.observaciones
    if data.precio is not None:
        trat.precio = data.precio
    if data.tratamiento is not None:
        trat.tratamiento = data.tratamiento
    if data.estado is not None:
        trat.estado = data.estado

    try:
        db.commit()
        db.refresh(trat)
        return trat
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al actualizar el tratamiento."
        )

def listar_agenda(db: Session, tratamiento_id: uuid.UUID, current_user: Usuario) -> List[AgendaTratamientos]:
    obtener_tratamiento_por_id(db, tratamiento_id, current_user)
    return db.query(AgendaTratamientos).filter(
        AgendaTratamientos.id_tratamiento_paciente == tratamiento_id
    ).all()

def crear_agenda(db: Session, data: AgendaTratamientoCreate, current_user: Usuario) -> AgendaTratamientos:
    role_val = current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)
    if role_val not in ("SYSTEM_ADMIN", "ODONTOLOGO"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores u odontólogos pueden agendar sesiones de tratamiento."
        )

    trat = db.query(TratamientoPaciente).filter(
        TratamientoPaciente.tratamiento_paciente_id == data.id_tratamiento_paciente
    ).first()
    if not trat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tratamiento no encontrado."
        )

    nueva_agenda = AgendaTratamientos(
        id_tratamiento_paciente=data.id_tratamiento_paciente,
        dia_semana=data.dia_semana,
        hora_inicio=data.hora_inicio,
        hora_fin=data.hora_fin,
        fecha_registro=datetime.now(timezone.utc)
    )

    try:
        db.add(nueva_agenda)
        db.commit()
        db.refresh(nueva_agenda)
        return nueva_agenda
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al crear la agenda del tratamiento."
        )
