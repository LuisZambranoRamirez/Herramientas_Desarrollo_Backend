import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importamos la aplicación principal, el router y las dependencias a sobreescribir
from app.main import app  # Asegúrate de que tu FastAPI() se instancie en app/main.py
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import Usuario

# 1. CONFIGURACIÓN DE BASE DE DATOS DE PRUEBAS (En memoria usando SQLite)
# Esto evita alterar tu base de datos real durante los tests.
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Fixture para simular la sesión de Base de Datos
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# 2. CONFIGURACIÓN DE UN USUARIO SIMULADO (MOCK) PARA /me
# Simulamos un usuario que ya pasó la validación del token jwt
def override_get_current_user():
    return Usuario(
        id=1,
        username="testuser",
        email="test@example.com",
        rol="paciente"
    )

# Aplicamos los "overrides" a la app antes de inicializar el cliente de pruebas
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

# --- CONFIGURACIÓN DE MOCKS PARA EL SERVICIO DE AUTENTICACIÓN ---
# Como no tenemos el código interno de 'auth_service', simulamos sus respuestas
@pytest.fixture(autouse=True)
def mock_auth_service(monkeypatch):
    from app.services import auth as auth_service
    
    # Simulamos lo que respondería iniciar_sesion
    def mock_iniciar_sesion(db, credentials):
        if credentials.username == "usuario_valido" and credentials.password == "secreto":
            return {
                "accessToken": "mocked-jwt-token",
                "user": {"id": 1, "username": "usuario_valido", "email": "test@test.com"}
            }
        # Puedes levantar una excepción personalizada si las credenciales fallan
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    # Simulamos lo que respondería registrar_paciente
    def mock_registrar_paciente(db, data):
        return {
            "id": 1,
            "username": data.username,
            "email": data.email,
            "mensaje": "Paciente registrado exitosamente"
        }

    # Reemplazamos las funciones reales por nuestros mocks durante la ejecución del test
    monkeypatch.setattr(auth_service, "iniciar_sesion", mock_iniciar_sesion)
    monkeypatch.setattr(auth_service, "registrar_paciente", mock_registrar_paciente)


# ==============================================================================
# 3. PRUEBAS UNITARIAS / INTEGRACIÓN
# ==============================================================================

def test_login_exitoso():
    payload = {"username": "usuario_valido", "password": "secreto"}
    response = client.post("/auth/login", json=payload)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "accessToken" in data
    assert data["user"]["username"] == "usuario_valido"


def test_login_fallido():
    payload = {"username": "usuario_incorrecto", "password": "wrong_password"}
    response = client.post("/auth/login", json=payload)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_registro_paciente_exitoso():
    # Ajusta este diccionario según los campos reales requeridos por tu esquema 'RegistroPaciente'
    payload = {
        "username": "nuevopaciente",
        "email": "paciente@correo.com",
        "password": "securepassword",
        "nombre": "Juan",
        "apellido": "Pérez"
    }
    response = client.post("/auth/register", json=payload)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "nuevopaciente"
    assert "id" in data


def test_obtener_perfil_me():
    # Al haber sobreescrito 'get_current_user', la ruta asume que estamos logueados automáticamente
    response = client.get("/auth/me")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
