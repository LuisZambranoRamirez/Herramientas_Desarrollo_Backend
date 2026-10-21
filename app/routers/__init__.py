from fastapi import APIRouter

from app.routers.auth import router as auth_router
from app.routers.paciente import router as paciente_router
from app.routers.odontologo import router as odontologo_router
from app.routers.cita import router as cita_router
from app.routers.tratamiento import router as tratamiento_router
from app.routers.pago import router as pago_router
from app.routers.insumo import router as insumo_router
from app.routers.proveedor import router as proveedor_router
from app.routers.usuario import router as usuario_router

# Router principal de la API: cada módulo nuevo se registra aquí
api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(paciente_router)
api_router.include_router(odontologo_router)
api_router.include_router(cita_router)
api_router.include_router(tratamiento_router)
api_router.include_router(pago_router)
api_router.include_router(insumo_router)
api_router.include_router(proveedor_router)
api_router.include_router(usuario_router)
