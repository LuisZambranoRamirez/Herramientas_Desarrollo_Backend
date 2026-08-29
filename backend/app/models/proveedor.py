from sqlalchemy import Column, String, Date
from app.database.connection import Base

class Proveedor(Base):
    __tablename__ = "proveedor"
    
    ruc = Column(String(11), primary_key=True)
    nombre = Column(String(255), nullable=False, unique=True)
    telefono = Column(String(9), nullable=False, unique=True)
    fecha_registro = Column(Date, nullable=False)