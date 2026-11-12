from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import config
from app.models.models import Base

DATABASE_URL = config.DATABASE_URL


# Normalizar la URL y eliminar parámetros no reconocidos
# por psycopg2.
url = make_url(DATABASE_URL)

query = dict(url.query)
query.pop("pgbouncer", None)
query.pop("supa", None)

url = url.set(query=query)

# Usar explícitamente el controlador psycopg2.
if url.drivername in ("postgres", "postgresql"):
    url = url.set(drivername="postgresql+psycopg2")

engine = create_engine(
    url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={"connect_timeout": 10},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def init_db():
    """Crea las tablas que aún no existan."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Proporciona una sesión de base de datos por petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()