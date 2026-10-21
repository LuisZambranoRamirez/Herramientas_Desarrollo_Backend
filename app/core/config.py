import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


def _require_env(name: str) -> str:
    """Devuelve el valor de una variable de entorno o falla de inmediato."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"La variable de entorno '{name}' es requerida y no está configurada. "
            f"Agrégala en tu archivo .env local."
        )
    return value


class Config:
    # --- Variables obligatorias (sin fallback) ---
    DATABASE_URL: str = _require_env("DATABASE_URL")
    SECRET_KEY: str = _require_env("SECRET_KEY")

    # --- Variables con valores por defecto seguros ---
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )  # 30 minutos por defecto por seguridad

    # --- CORS: orígenes permitidos (separados por coma) ---
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]


# Instancia de Configuración
config = Config()