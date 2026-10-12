import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = (
        os.getenv("POSTGRES_PRISMA_URL")
        or "postgresql+psycopg2://postgres:drakotako1234@localhost:5432/SoliDent"
    )
    SECRET_KEY = (
        os.getenv("SECRET_KEY")
        or "soident-secret-key-change-in-production"
    )

    ALGORITHM = (
        os.getenv("ALGORITHM")
        or "HS256"
    )

    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
        or "480"
    )  # 8 horas por defecto
    
# Instancia de Configuración
config = Config()