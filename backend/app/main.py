from fastapi import FastAPI
from app.database.connection import engine, Base
from app.models import (
    usuario, personal, paciente, odontologo, 
    cita, tratamiento, insumo, proveedor, pago
)

app = FastAPI(title="Soident API", version="1.0.0")

@app.on_event("startup")
def startup():
    # Crear todas las tablas en la base de datos
    Base.metadata.create_all(bind=engine)
    print("✅ Base de datos inicializada")

@app.get("/")
def root():
    return {"message": "Soident API funcionando 🦷"}

@app.get("/health")
def health():
    return {"status": "OK", "service": "Soident Backend"}