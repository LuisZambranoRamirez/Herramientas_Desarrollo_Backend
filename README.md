# Herramientas_Desarrollo_Backend

API Backend del sistema odontológico **Solident** (FastAPI + SQLAlchemy + PostgreSQL).

## Estructura

```
.
├── .env.example          # Variables de entorno de ejemplo (copiar a .env)
├── requirements.txt
├── seed.py               # Carga usuarios, paciente y odontólogos de prueba
├── documentation/        # Script SQL (apolo.sql) y diagrama del esquema
└── app/
    ├── main.py           # Crea la app, CORS, arranque e inclusión de api_router
    ├── core/             # Config, conexión a BD, seguridad (JWT, hash), dependencias, manejo de errores
    ├── models/           # Tablas (modelos SQLAlchemy)
    ├── schemas/          # Entrada y salida de la API (Pydantic)
    ├── services/         # Lógica de negocio: validaciones, permisos y consultas
    └── routers/          # Endpoints HTTP; solo reciben la petición y llaman al servicio
```

Flujo de una petición: `routers` → `services` → `models` / `core.database`.

> **Nota sobre `Odontologo`:** hereda de `Personal` (herencia por tablas unidas). Un objeto `Odontologo`
> ya trae `nombres`, `apellidos`, `telefono`, `correo`, `activo` y `fecha_registro`; no hay que hacer
> `JOIN` con `Personal` ni existe `odontologo.personal`. Para crear uno basta con instanciar `Odontologo(...)`.

## Cómo agregar un módulo nuevo

1. Modelo en `app/models/models.py` (o un archivo nuevo importado en `app/models/__init__.py`).
2. Esquemas en `app/schemas/<modulo>.py`.
3. Lógica en `app/services/<modulo>.py`.
4. Endpoints en `app/routers/<modulo>.py` y registrar el router en `app/routers/__init__.py`.

## Instalación y ejecución

### 1. Base de datos PostgreSQL

Crea una base de datos vacía (por ejemplo `SoliDent`). Las tablas se crean solas al iniciar la API
(`init_db()`), o puedes usar `documentation/apolo.sql`.

### 2. Variables de entorno

Copia `.env.example` a `.env` y completa tus datos. **Es obligatorio definir `DATABASE_URL`**
(no hay credenciales escritas en el código):

```
DATABASE_URL=postgresql+psycopg2://postgres:tu_password@localhost:5432/SoliDent
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Si el frontend corre en otra URL (otro puerto, Vercel, etc.) agrégala a `CORS_ORIGINS`.

### 3. Entorno virtual e instalación

Windows (PowerShell):

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Cargar datos de prueba

```bash
python seed.py
```

Crea (si no existen) estos usuarios:

| Rol          | Usuario               | Contraseña          |
|--------------|-----------------------|---------------------|
| SYSTEM_ADMIN | `admin`               | `AdminPassword123!` |
| PACIENTE     | `paciente@correo.com` | `password123`       |
| ODONTOLOGO   | `dr.mendoza`          | `Doctor123!`        |
| ODONTOLOGO   | `dra.paredes`         | `Doctor123!`        |

### 5. Iniciar el servidor

```bash
uvicorn app.main:app --reload
```

## Acceso a la API

- API: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Health check: <http://localhost:8000/api/health>

Todas las rutas cuelgan de `/api` (`/api/auth`, `/api/pacientes`, `/api/odontologos`, `/api/citas`).
Las rutas protegidas requieren el header `Authorization: Bearer <accessToken>` obtenido en `POST /api/auth/login`.

### Endpoints de citas

| Método | Ruta                       | Descripción                                             |
|--------|----------------------------|---------------------------------------------------------|
| GET    | `/api/citas/odontologos`   | Odontólogos activos (público, para elegir al agendar)   |
| POST   | `/api/citas`               | Agendar cita (409 si el odontólogo ya tiene esa hora)   |
| GET    | `/api/citas`               | Listar con filtros `fecha`, `estado`, `dni_paciente`, `dni_odontologo` |
| GET    | `/api/citas/mis-citas`     | Citas del usuario conectado                             |
| GET    | `/api/citas/{id}`          | Detalle de una cita                                     |
| PUT    | `/api/citas/{id}`          | Editar / reprogramar (admin y odontólogo)               |
| PATCH  | `/api/citas/{id}/estado`   | Cambiar estado                                          |
| PATCH  | `/api/citas/{id}/cancelar` | Cancelar                                                |

## Actualizar las dependencias

Después de instalar una nueva librería:

```bash
pip freeze > requirements.txt
```
