from sqlalchemy import Column, String, ForeignKey, UUID, Enum, Numeric, Date
from sqlalchemy.orm import relationship
from app.database.connection import Base
import enum
import uuid

class MetodoPago(enum.Enum):
    EFECTIVO = "efectivo"
    DIGITAL = "digital"

class Pago(Base):
    __tablename__ = "pago"
    
    pago_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    id_tratamiento_paciente = Column(UUID, ForeignKey("tratamiento_paciente.tratamiento_paciente_id"), nullable=False)
    monto = Column(Numeric(10,2), nullable=False)
    metodo_pago = Column(Enum(MetodoPago), nullable=False)
    fecha_registro = Column(Date, nullable=False)
    
    # Relaciones
    tratamiento = relationship("TratamientoPaciente", back_populates="pagos")