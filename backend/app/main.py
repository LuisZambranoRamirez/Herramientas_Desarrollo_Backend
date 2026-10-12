from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import engine, Base
from app.routers import api_router
from app.core.exception_handlers import register_exception_handlers
from contextlib import asynccontextmanager
from app.database.connection import init_db

app = FastAPI(
    title="Solident API",
    version="1.0.0",
    description="API Backend para el sistema odontológico Solident"
)

register_exception_handlers(app)

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Base de datos inicializada correctamente")
    yield

@app.get("/")
def root():
    return {"message": "Solident API funcionando"}

# Endpoint simple GET /api/health
@app.get("/api/health")
def api_health():
    return {"status": "ok"}

# Incluir routers bajo el prefijo /api
app.include_router(api_router)
