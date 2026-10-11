Instalación y ejecución
Windows (PowerShell)

Ejecuta los siguientes comandos desde la raíz del repositorio:

# 1. Crear el entorno virtual en la raíz del repositorio
python -m venv .venv

# 2. Activar el entorno virtual
.\.venv\Scripts\Activate.ps1

# 3. Instalar las dependencias del backend
pip install -r .\backend\requirements.txt

# 4. Crear el archivo .env a partir del archivo de ejemplo
Copy-Item .env.example .env

# 5. Entrar en la carpeta del backend
cd backend

# 6. Iniciar el servidor de desarrollo
uvicorn app.main:app --reload

Linux (Bash)

Ejecuta los siguientes comandos desde la raíz del repositorio:

# 1. Crear el entorno virtual en la raíz del repositorio
python3 -m venv .venv

# 2. Activar el entorno virtual
source .venv/bin/activate

# 3. Instalar las dependencias del backend
pip install -r backend/requirements.txt

# 4. Crear el archivo .env a partir del archivo de ejemplo
cp .env.example .env

# 5. Entrar en la carpeta del backend
cd backend

# 6. Iniciar el servidor de desarrollo
uvicorn app.main:app --reload

Importante: estos comandos asumen que .env.example está en la raíz del repositorio. Antes de iniciar el servidor, configura en .env las credenciales y variables necesarias para MySQL. Si el archivo .env se crea por primera vez, revisa que no exista ya para evitar sobrescribir tu configuración.
Acceso a la API

Cuando el servidor esté iniciado, abre en el navegador:

API: http://localhost:8000
Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
Cargar datos de prueba

Con el entorno virtual activado, ejecuta desde la carpeta backend/:

# Cargar usuarios y datos de prueba en la base de datos
python seed.py

Actualizar las dependencias

Después de instalar una nueva librería, ejecuta desde backend/:

# Guardar las dependencias instaladas y sus versiones
pip freeze > requirements.txt