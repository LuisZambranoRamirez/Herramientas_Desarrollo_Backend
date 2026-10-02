import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Date, Time, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database.connection import Base

class EstadoCita(str, enum.Enum):
    PROGRAMADA = "PROGRAMADA"
    CONFIRMADA = "CONFIRMADA"
    ATENDIDA = "ATENDIDA"
    CANCELADA = "CANCELADA"
    NO_ASISTIO = "NO_ASISTIO"
    REPROGRAMADA = "REPROGRAMADA"
    EN_PROCESO = "EN_PROCESO"

class Cita(Base):
    __tablename__ = "cita"
    
    cita_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dni_paciente = Column(String(8), ForeignKey("paciente.dni"), nullable=False)
    dni_odontologo = Column(String(8), ForeignKey("odontologo.dni"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    motivo_consulta = Column(String(255), nullable=False)
    diagnostico = Column(String(255), nullable=True)
    estado = Column(String(50), nullable=False, default=EstadoCita.PROGRAMADA.value)
    fecha_registro = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relaciones
    paciente = relationship("Paciente", back_populates="citas")
    odontologo = relationship("Odontologo", back_populates="citas")