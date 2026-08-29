from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Personal(Base):
    __tablename__ = "personal"
    
    dni = Column(String(8), primary_key=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    telefono = Column(String(9), nullable=False, unique=True)
    correo = Column(String(150), nullable=False, unique=True)
    activo = Column(Boolean, nullable=False, default=True)
    fecha_registro = Column(DateTime, nullable=False)
    
    odontologo = relationship("Odontologo", back_populates="personal", uselist=False)