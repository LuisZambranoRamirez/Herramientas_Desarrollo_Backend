import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        "mysql+pymysql://root@localhost:3306/solident_db"
    )
    SECRET_KEY = os.getenv("SECRET_KEY", "soident-secret-key-change-in-production")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # 8 horas por defecto

# Instancia de Configuración
config = Config()