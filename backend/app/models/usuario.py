from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from app.database.connection import Base
import enum

class UserRole(enum.Enum):
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    ODONTOLOGO = "ODONTOLOGO"
    PACIENTE = "PACIENTE"

class Usuario(Base):
    __tablename__ = "usuario"
    
    username = Column(String(50), primary_key=True)
    password = Column(String(255), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    user_role = Column(Enum(UserRole), nullable=False)
    fecha_registro = Column(DateTime, nullable=False)
    
    paciente = relationship("Paciente", back_populates="usuario", uselist=False)
    odontologo = relationship("Odontologo", back_populates="usuario", uselist=False)