from sqlalchemy import Column, String, UUID, Numeric, Date
from app.database.connection import Base
import uuid

class Insumo(Base):
    __tablename__ = "insumo"
    
    insumo_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    nombre = Column(String(150), nullable=False, unique=True)
    stock = Column(Numeric(10,2), nullable=False)
    stock_minimo = Column(Numeric(10,2), nullable=False)
    fecha_vencimiento = Column(Date, nullable=True)
    fecha_registro = Column(Date, nullable=False)