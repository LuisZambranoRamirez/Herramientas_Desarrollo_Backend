# Instalación y ejecución

## Windows (PowerShell)

Ejecuta los siguientes comandos desde la raíz del repositorio:

```bash
# Crear el entorno virtual
python -m venv .venv

# Activar el entorno virtual
.venv\Scripts\Activate.ps1

# Instalar las dependencias
pip install -r backend/requirements.txt

# Entrar en la carpeta del backend
cd backend

# Iniciar el servidor de desarrollo
uvicorn app.main:app --reload
````

## Linux (Bash)

Ejecuta los siguientes comandos desde la raíz del repositorio:

bash
```
# Crear el entorno virtual
python3 -m venv .venv

# Activar el entorno virtual
source .venv/bin/activate

# Instalar las dependencias
pip install -r backend/requirements.txt

# Entrar en la carpeta del backend
cd backend

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