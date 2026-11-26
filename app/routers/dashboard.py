from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.models import Usuario, UserRoleEnum
from app.schemas.dashboard import DashboardResumenResponse
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/resumen",
    response_model=DashboardResumenResponse,
    summary="Resumen del panel principal del administrador",
)
def obtener_resumen_dashboard(
    current_user: Usuario = Depends(require_roles(UserRoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    return dashboard_service.obtener_resumen(db, current_user)