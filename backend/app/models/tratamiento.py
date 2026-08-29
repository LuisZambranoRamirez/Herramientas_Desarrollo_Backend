from sqlalchemy import Column, String, ForeignKey, UUID, Enum, Numeric, Text, Date
from sqlalchemy.orm import relationship
from app.database.connection import Base
import enum
import uuid

class TratamientoOdontologico(enum.Enum):
    LIMPIEZA_DENTAL_PROFUNDA = "Limpieza_dental_profunda"
    APLICACION_DE_FLUOR = "Aplicacion_de_fluor"
    SELLADORES = "Selladores_de_fosas_y_fisuras"
    RESTAURACION_CON_RESINA = "Restauracion_con_resina"
    ORTOPEDIA_MAXILAR = "Ortopedia_maxilar"
    IMPLANTE_DENTAL = "Implante_dental"

class EstadoTratamiento(enum.Enum):
    INICIADO = "INICIADO"
    EN_PROCESO = "EN_PROCESO"
    FINALIZADO = "FINALIZADO"
    PENDIENTE = "PENDIENTE"

class TratamientoPaciente(Base):
    __tablename__ = "tratamiento_paciente"
    
    tratamiento_paciente_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    dni_paciente = Column(String(8), ForeignKey("paciente.dni"), nullable=False)
    dni_odontologo = Column(String(8), ForeignKey("odontologo.dni"), nullable=False)
    observaciones = Column(Text, nullable=False, default="")
    precio = Column(Numeric(10,2), nullable=False)
    tratamiento = Column(Enum(TratamientoOdontologico), nullable=False)
    estado = Column(Enum(EstadoTratamiento), nullable=False, default=EstadoTratamiento.PENDIENTE)
    fecha_registro = Column(Date, nullable=False)
    
    paciente = relationship("Paciente", back_populates="tratamientos")
    odontologo = relationship("Odontologo", back_populates="tratamientos")
    pagos = relationship("Pago", back_populates="tratamiento")