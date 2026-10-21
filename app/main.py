from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import api_router
from app.core.exception_handlers import register_exception_handlers
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.core.config import config

# 1. Definimos el lifespan PRIMERO para que exista antes de usarlo
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Base de datos inicializada correctamente")
    yield

# 2. Ahora sí podemos pasarle el lifespan a la app
app = FastAPI(
    title="Solident API",
    version="1.0.0",
    description="API Backend para el sistema odontológico Solident",
    lifespan=lifespan  
)

register_exception_handlers(app)

# Middleware de CORS para conexión con frontend (Vue 3 / Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Solident API funcionando"}

# Endpoint simple GET /api/health
@app.get("/api/health")
def api_health():
    return {"status": "ok"}

# Incluir routers bajo el prefijo /api
app.include_router(api_router)
