from fastapi import APIRouter

from app.routers.auth import router as auth_router
from app.routers.paciente import router as paciente_router
from app.routers.odontologo import router as odontologo_router
from app.routers.cita import router as cita_router

# Router principal de la API: cada módulo nuevo se registra aquí
api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(paciente_router)
api_router.include_router(odontologo_router)
api_router.include_router(cita_router)
