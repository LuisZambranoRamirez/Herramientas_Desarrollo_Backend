
# SoliDent - Backend API

API backend del sistema odontológico SoliDent, desarrollada con FastAPI y SQLAlchemy.

## Estructura del proyecto

```text
.
├── app/
│   ├── core/           # Configuración y componentes compartidos
│   ├── models/         # Modelos de datos
│   ├── routers/        # Endpoints de la API
│   ├── schemas/        # Esquemas de entrada y salida
│   ├── services/       # Lógica de negocio
│   └── main.py         # Aplicación FastAPI
├── documentation/
│   ├── apolo.sql       # Script SQL disponible
│   └── diagrama.png    # Diagrama de base de datos
├── requirements.txt
├── seed.py
└── README.md
```

## Requisitos previos

- Python instalado.
- Base de datos PostgreSQL configurada.
- Variables de entorno configuradas en `.env`.

## Instalación y ejecución

Ejecuta los comandos desde la raíz del repositorio.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Linux (Bash)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

## Variables de entorno

Configura en `.env` las variables necesarias:

- `DATABASE_URL`, `POSTGRES_PRISMA_URL` o `POSTGRES_URL`: conexión a la base de datos.
- `SECRET_KEY`: clave de autenticación.
- `ALGORITHM`: algoritmo de tokens; por defecto, `HS256`.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: duración del token en minutos; por defecto, `480`.

No compartas ni publiques las credenciales del archivo `.env`.

## Acceso a la API

Con el servidor iniciado:

- API raíz: http://127.0.0.1:8000/
- Estado de la API: http://127.0.0.1:8000/api/health
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Base de datos

El directorio `documentation/` contiene el script SQL y el diagrama disponibles en el repositorio. Revisa el esquema antes de realizar cambios en la base de datos.

## Buenas prácticas

- Revisa los cambios antes de crear un commit.
- Ejecuta las pruebas disponibles antes de publicar cambios.
- No subas credenciales ni archivos `.env`.
- Coordina con el equipo antes de modificar la configuración compartida.
