from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import config
from app.models.models import Base

DATABASE_URL = config.DATABASE_URL

if not DATABASE_URL:
    raise RuntimeError("La variable DATABASE_URL no está configurada")

# Compatibilidad con URLs de PostgreSQL de Supabase.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+psycopg2://",
        1,
    )
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg2://",
        1,
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=2,
    max_overflow=0,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def init_db():
    """Crea las tablas que aún no existan según los modelos registrados."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Proporciona una sesión de base de datos por petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()