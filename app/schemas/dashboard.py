from pydantic import BaseModel


class DashboardResumenResponse(BaseModel):
    citas_hoy: int
    pacientes_total: int
    tratamientos_en_proceso: int
    insumos_stock_bajo: int