HerramientasDesarrolloBackend

API Backend del sistema odontológico Solident, desarrollado con FastAPI, SQLAlchemy y MySQL.

Estructura del proyecto
.
├── .env.example          # Variables de entorno de ejemplo (copiar a .env)
├── .venv/                # Entorno virtual de Python (fuera de backend)
├── SQL/                  # Script y diagrama del esquema de base de datos
└── backend/
    ├── requirements.txt  # Dependencias del proyecto
    ├── seed.py           # Carga usuarios y datos de prueba
    └── app/
        ├── main.py       # Crea la app, configura CORS e incluye api_router
        ├── config.py     # Lectura de variables de entorno
        ├── core/         # Seguridad (JWT, hash) y dependencias
        ├── database/     # Motor, sesión y Base de SQLAlchemy
        ├── models/       # Modelos de tablas SQLAlchemy
        ├── schemas/      # Esquemas de entrada y salida (Pydantic)
        ├── services/     # Lógica de negocio, validaciones y consultas
        └── routers/      # Endpoints HTTP de la API


Flujo de una petición: routers → services → models / database.

Instalación y ejecución
1. Crear el entorno virtual

Abre una terminal en la carpeta raíz del repositorio, donde se encuentran SQL/ y backend/.

Windows (PowerShell):

python -m venv .venv


Linux (Bash):

python3 -m venv .venv


El entorno virtual se creará en .venv/, fuera de backend/.

2. Activar el entorno virtual

Windows (PowerShell):

.\.venv\Scripts\Activate.ps1


Linux (Bash):

source .venv/bin/activate


Una vez activado, la terminal mostrará normalmente (.venv) al inicio de la línea.

3. Instalar las dependencias

Desde la raíz del repositorio, entra en la carpeta backend:

cd backend


Instala las dependencias con el entorno virtual activado:

pip install -r requirements.txt

4. Configurar las variables de entorno

En la raíz del repositorio, copia .env.example y crea un archivo .env con la configuración correspondiente.

Windows (PowerShell):

Copy-Item .env.example .env


Linux (Bash):

cp .env.example .env


Completa las variables necesarias para la conexión a MySQL y las demás configuraciones requeridas por el proyecto.

Importante: el archivo .env debe permanecer en la ubicación que espera app/config.py. Si la configuración busca el archivo en otra ruta, ajusta su ubicación según el código del proyecto.
5. Ejecutar el backend

Asegúrate de estar dentro de la carpeta backend, con el entorno virtual activado.

Windows (PowerShell) y Linux (Bash):

uvicorn app.main:app --reload


El servidor se iniciará en modo de desarrollo.

6. Abrir la documentación de la API
API: http://localhost:8000
Documentación interactiva de Swagger: http://localhost:8000/docs
Documentación alternativa de ReDoc: http://localhost:8000/redoc
Cargar datos de prueba

Para cargar los usuarios y los datos de prueba, ejecuta el siguiente comando desde la carpeta backend/, con el entorno virtual activado:

Windows (PowerShell) y Linux (Bash):

python seed.py


Asegúrate de haber configurado correctamente la conexión a MySQL antes de ejecutar el script.

Cómo agregar un módulo nuevo
Crear el modelo en app/models/<modulo>.py e importarlo en app/models/__init__.py.
Crear los esquemas en app/schemas/<modulo>.py.
Implementar la lógica de negocio en app/services/<modulo>.py.
Crear los endpoints en app/routers/<modulo>.py.
Registrar el router en app/routers/__init__.py.
Mantenimiento de dependencias

Cuando se instale una nueva librería, actualiza requirements.txt con el entorno virtual activado y desde la carpeta backend/.

Windows (PowerShell) y Linux (Bash):

pip freeze > requirements.txt


Este comando guarda las dependencias instaladas y sus versiones actuales en requirements.txt.

Notas importantes
El entorno virtual .venv se encuentra en la raíz del repositorio, al mismo nivel que backend/ y SQL/.
Activa el entorno virtual antes de instalar dependencias, ejecutar el servidor o cargar datos de prueba.
Ejecuta los comandos de Uvicorn y seed.py desde la carpeta backend/.
No subas .venv/, .env ni otros archivos con credenciales al repositorio. Añádelos a .gitignore.
Mantén .env.example actualizado con los nombres de las variables necesarias, pero sin credenciales reales.