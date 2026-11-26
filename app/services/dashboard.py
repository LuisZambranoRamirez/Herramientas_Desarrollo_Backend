from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import (
    Cita,
    EstadoCitaEnum,
    EstadoTratamientoEnum,
    Insumo,
    Paciente,
    TratamientoPaciente,
    Usuario,
)
from app.schemas.dashboard import DashboardResumenResponse

ZONA_LIMA = timezone(timedelta(hours=-5))


def obtener_resumen(db: Session, current_user: Usuario) -> DashboardResumenResponse:
    role_val = (current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)).upper()
    if role_val not in ("SYSTEM_ADMIN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción"
        )

    hoy = datetime.now(ZONA_LIMA).date()

    citas_hoy = db.query(func.count(Cita.cita_id)).filter(
        Cita.fecha == hoy,
        Cita.estado != EstadoCitaEnum.CANCELADA
    ).scalar()

    pacientes_total = db.query(func.count(Paciente.dni)).scalar()

    tratamientos_en_proceso = db.query(func.count(TratamientoPaciente.tratamiento_paciente_id)).filter(
        TratamientoPaciente.estado == EstadoTratamientoEnum.EN_PROCESO
    ).scalar()

    insumos_stock_bajo = db.query(func.count(Insumo.insumo_id)).filter(
        Insumo.stock <= Insumo.stock_minimo
    ).scalar()

    return DashboardResumenResponse(
        citas_hoy=citas_hoy,
        pacientes_total=pacientes_total,
        tratamientos_en_proceso=tratamientos_en_proceso,
        insumos_stock_bajo=insumos_stock_bajo,
    )