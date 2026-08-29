from sqlalchemy import Column, String, Date, Time, ForeignKey, UUID, Enum
from sqlalchemy.orm import relationship
from app.database.connection import Base
import enum
import uuid

class EstadoCita(enum.Enum):
    PROGRAMADA = "PROGRAMADA"
    CONFIRMADA = "CONFIRMADA"
    ATENDIDA = "ATENDIDA"
    CANCELADA = "CANCELADA"
    NO_ASISTIO = "NO_ASISTIO"
    REPROGRAMADA = "REPROGRAMADA"
    EN_PROCESO = "EN_PROCESO"

class Cita(Base):
    __tablename__ = "cita"
    
    cita_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    dni_paciente = Column(String(8), ForeignKey("paciente.dni"), nullable=False)
    dni_odontologo = Column(String(8), ForeignKey("odontologo.dni"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    motivo_consulta = Column(String(255), nullable=False)
    diagnostico = Column(String(255), nullable=True)
    estado = Column(Enum(EstadoCita), nullable=False, default=EstadoCita.PROGRAMADA)
    fecha_registro = Column(Date, nullable=False)
    
    # Relaciones
    paciente = relationship("Paciente", back_populates="citas")
    odontologo = relationship("Odontologo", back_populates="citas")