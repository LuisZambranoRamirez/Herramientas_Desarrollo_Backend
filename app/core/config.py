import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL: str = (
        os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_PRISMA_URL")
        or os.getenv("POSTGRES_URL")
        or "aqui va tu URL de conexión a PostgreSQL local"
    )

    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480")
    )

# Borrar esto en produccion y colocar el dominio de tu frontend en la lista de CORS_ORIGINS
    CORS_ORIGINS: list[str] = [
        "*"
    ]

config = Config()

if not config.DATABASE_URL or config.DATABASE_URL == (
    "aqui va tu URL de conexión a PostgreSQL local"
):
    raise RuntimeError(
        "No se encontró una URL válida de PostgreSQL. "
        "Configura DATABASE_URL, POSTGRES_PRISMA_URL o POSTGRES_URL."
    )

if not config.SECRET_KEY:
    raise RuntimeError("La variable SECRET_KEY no está configurada.")
