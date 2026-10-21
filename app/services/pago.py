import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Pago, TratamientoPaciente, Usuario, Paciente
from app.schemas.pago import PagoCreate

def listar_pagos(db: Session, current_user: Usuario, tratamiento_id: Optional[uuid.UUID] = None) -> List[Pago]:
    query = db.query(Pago)

    role_val = current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)
    if role_val == "PACIENTE":
        pac = db.query(Paciente).filter(Paciente.username == current_user.username).first()
        if not pac:
            return []
        query = query.join(TratamientoPaciente).filter(TratamientoPaciente.dni_paciente == pac.dni)
    elif tratamiento_id:
        query = query.filter(Pago.id_tratamiento_paciente == tratamiento_id)

    return query.order_by(Pago.fecha_registro.desc()).all()

def obtener_pago_por_id(db: Session, pago_id: uuid.UUID, current_user: Usuario) -> Pago:
    pago = db.query(Pago).filter(Pago.pago_id == pago_id).first()
    if not pago:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado."
        )

    role_val = current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)
    if role_val == "PACIENTE":
        trat = db.query(TratamientoPaciente).filter(TratamientoPaciente.tratamiento_paciente_id == pago.id_tratamiento_paciente).first()
        pac = db.query(Paciente).filter(Paciente.username == current_user.username).first()
        if not pac or not trat or trat.dni_paciente != pac.dni:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver este comprobante de pago."
            )

    return pago

def registrar_pago(db: Session, data: PagoCreate, current_user: Usuario) -> Pago:
    role_val = current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)
    if role_val != "SYSTEM_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden registrar pagos."
        )

    trat = db.query(TratamientoPaciente).filter(
        TratamientoPaciente.tratamiento_paciente_id == data.id_tratamiento_paciente
    ).first()
    if not trat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tratamiento asociado no encontrado."
        )

    nuevo_pago = Pago(
        id_tratamiento_paciente=data.id_tratamiento_paciente,
        monto=data.monto,
        metodo_pago=data.metodo_pago,
        fecha_registro=datetime.now(timezone.utc)
    )

    try:
        db.add(nuevo_pago)
        db.commit()
        db.refresh(nuevo_pago)
        return nuevo_pago
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al registrar el pago."
        )
