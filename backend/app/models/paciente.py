from sqlalchemy import Column, String, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Paciente(Base):
    __tablename__ = "paciente"
    
    dni = Column(String(8), primary_key=True)
    username = Column(String(50), ForeignKey("usuario.username"), nullable=False, unique=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    direccion = Column(String(200), unique=True)
    telefono = Column(String(9), unique=True)
    correo = Column(String(150), unique=True)
    observaciones = Column(Text, nullable=False, default="")
    fecha_nacimiento = Column(Date, nullable=False)
    fecha_registro = Column(DateTime, nullable=False)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="paciente")
    citas = relationship("Cita", back_populates="paciente")
    tratamientos = relationship("TratamientoPaciente", back_populates="paciente")