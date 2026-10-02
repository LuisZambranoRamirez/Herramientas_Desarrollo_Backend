import enum
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Especialidad(str, enum.Enum):
    ORTODONCIA = "ORTODONCIA"
    ENDODONCIA = "ENDODONCIA"
    PERIODONCIA = "PERIODONCIA"
    ODONTOPEDIATRIA = "ODONTOPEDIATRIA"
    CIRUGIA_MAXILOFACIAL = "CIRUGIA_MAXILOFACIAL"
    IMPLANTOLOGIA = "IMPLANTOLOGIA"
    REHABILITACION_ORAL = "REHABILITACION_ORAL"
    ODONTOLOGIA_ESTETICA = "ODONTOLOGIA_ESTETICA"

class Odontologo(Base):
    __tablename__ = "odontologo"
    
    dni = Column(String(8), ForeignKey("personal.dni"), primary_key=True)
    colegiatura = Column(String(50), nullable=False, unique=True)
    especialidad = Column(String(50), nullable=False)
    username = Column(String(50), ForeignKey("usuario.username"), nullable=False, unique=True)
    
    personal = relationship("Personal", back_populates="odontologo")
    usuario = relationship("Usuario", back_populates="odontologo")
    citas = relationship("Cita", back_populates="odontologo")
    tratamientos = relationship("TratamientoPaciente", back_populates="odontologo")