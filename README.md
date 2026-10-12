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

## Instalación y ejecución

### Windows (PowerShell)

Ejecuta los siguientes comandos desde la raíz del repositorio:

```bash
# Crear el entorno virtual
python -m venv .venv

# Activar el entorno virtual
.venv\Scripts\Activate.ps1

# Instalar las dependencias
pip install -r requirements.txt

# Iniciar el servidor de desarrollo
uvicorn app.main:app --reload
````

### Linux (Bash)

Ejecuta los siguientes comandos desde la raíz del repositorio:

bash
```
# Crear el entorno virtual
python3 -m venv .venv

# Activar el entorno virtual
source .venv/bin/activate

# Instalar las dependencias
pip install -r requirements.txt

# Iniciar el servidor de desarrollo
uvicorn app.main:app --reload
```

Importante: estos comandos asumen que el archivo `requirements.txt` se encuentra en `backend/`. Configura las variables de entorno necesarias en `.env` antes de iniciar el servidor.

## Acceso a la API

Cuando el servidor esté iniciado, abre en el navegador:

- API: [http://localhost:8000](<http://localhost:8000>)
- Swagger UI: [http://localhost:8000/docs](<http://localhost:8000/docs>)
- ReDoc: [http://localhost:8000/redoc](<http://localhost:8000/redoc>)

## Cargar datos de prueba

Con el entorno virtual activado, ejecuta desde la carpeta `backend/`:

bash
```
# Cargar usuarios y datos de prueba en la base de datos
python seed.py
```

## Actualizar las dependencias

Después de instalar una nueva librería, ejecuta desde `backend/`:

bash
```
# Guardar las dependencias instaladas y sus versiones
pip freeze > requirements.txt
```