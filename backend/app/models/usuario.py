import enum
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database.connection import Base
from app.core.security import get_password_hash, verify_password

class UserRole(str, enum.Enum):
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    ODONTOLOGO = "ODONTOLOGO"
    PACIENTE = "PACIENTE"

class Usuario(Base):
    __tablename__ = "usuario"

    username = Column(String(50), primary_key=True, index=True)
    password = Column(String(255), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    user_role = Column(String(50), nullable=False, default=UserRole.SYSTEM_ADMIN.value)
    fecha_registro = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relaciones con otros modelos del sistema
    paciente = relationship("Paciente", back_populates="usuario", uselist=False)
    odontologo = relationship("Odontologo", back_populates="usuario", uselist=False)

    def set_password(self, raw_password: str) -> None:
        """Encripta y asigna la contraseña usando bcrypt."""
        self.password = get_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Verifica la contraseña ingresada contra el hash encriptado."""
        return verify_password(raw_password, self.password)