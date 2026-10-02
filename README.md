# Herramientas_Desarrollo_Backend

API Backend del sistema odontológico Solident (FastAPI + SQLAlchemy + MySQL).

## Estructura

```
.
├── .env.example          # Variables de entorno de ejemplo (copiar a .env)
├── SQL/                  # Script y diagrama del esquema de base de datos
└── backend/
    ├── requirements.txt
    ├── seed.py           # Carga usuarios y datos de prueba
    └── app/
        ├── main.py       # Crea la app, CORS, arranque e inclusión de api_router
        ├── config.py     # Lectura de variables de entorno
        ├── core/         # Piezas transversales: seguridad (JWT, hash) y dependencias (get_current_user)
        ├── database/     # Motor, sesión y Base de SQLAlchemy
        ├── models/       # Tablas (modelos SQLAlchemy)
        ├── schemas/      # Entrada y salida de la API (Pydantic)
        ├── services/     # Lógica de negocio: validaciones, permisos y consultas
        └── routers/      # Endpoints HTTP; solo reciben la petición y llaman al servicio
```

Flujo de una petición: `routers` → `services` → `models` / `database`.

## Cómo agregar un módulo nuevo

1. Modelo en `app/models/<modulo>.py` e importarlo en `app/models/__init__.py`.
2. Esquemas en `app/schemas/<modulo>.py`.
3. Lógica en `app/services/<modulo>.py`.
4. Endpoints en `app/routers/<modulo>.py` y registrar el router en `app/routers/__init__.py`.

## Ejecución

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Datos de prueba: `python seed.py` (desde `backend/`).

Documentación interactiva: http://localhost:8000/docs
