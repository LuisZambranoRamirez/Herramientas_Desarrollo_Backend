from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import engine, Base
from app.routers.auth import router as auth_router
from app.routers.cita import router as cita_router
from app.models import (
    usuario, personal, paciente, odontologo, 
    cita, tratamiento, insumo, proveedor, pago
)

app = FastAPI(
    title="Solident API",
    version="1.0.0",
    description="API Backend para el sistema odontológico Solident"
)

# Middleware de CORS para conexión con frontend en Vue 3
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    """Intenta inicializar las tablas de la base de datos al arrancar."""
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Base de datos conectada e inicializada correctamente")
    except Exception as e:
        print(f"[AVISO] No se pudo conectar a la base de datos en el inicio: {e}")

@app.get("/")
def root():
    return {"message": "Solident API funcionando"}

# Endpoint simple GET /api/health
@app.get("/api/health")
def api_health():
    return {"status": "ok"}

# Incluir routers bajo el prefijo /api
app.include_router(auth_router, prefix="/api")
app.include_router(cita_router, prefix="/api")