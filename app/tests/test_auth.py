
from datetime import datetime, timezone, date

from fastapi import status

from app.models.models import Usuario, UserRoleEnum
from app.core.security import (
    get_password_hash,
    create_access_token,
)


def test_login_exitoso(client, db_session):
    usuario = Usuario(
        username="usuario_valido",
        password=get_password_hash("secreto123"),
        activo=True,
        user_role=UserRoleEnum.PACIENTE,
        fecha_registro=datetime.now(timezone.utc),
    )

    db_session.add(usuario)
    db_session.commit()

    response = client.post(
        "/api/auth/login",
        json={
            "username": "usuario_valido",
            "password": "secreto123",
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert "accessToken" in data
    assert data["user"]["username"] == "usuario_valido"
    assert data["user"]["user_role"] == "PACIENTE"


def test_login_fallido(client):
    response = client.post(
        "/api/auth/login",
        json={
            "username": "usuario_incorrecto",
            "password": "clave_incorrecta",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_registro_paciente_exitoso(client):
    payload = {
        "username": "nuevopaciente",
        "password": "ClaveSegura123",
        "dni": "12345678",
        "nombres": "Juan",
        "apellidos": "Perez",
        "telefono": "987654321",
        "correo": "juan@example.com",
        "fecha_nacimiento": "2000-05-15",
        "direccion": "Av. Los Olivos 123",
    }

    response = client.post(
        "/api/auth/register",
        json=payload,
    )

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    assert data["message"] == "Paciente registrado exitosamente"
    assert data["user"]["username"] == "nuevopaciente"
    assert data["user"]["user_role"] == "PACIENTE"
    assert data["user"]["activo"] is True
    assert "accessToken" in data


def test_registro_paciente_password_debil_rechazado(client):
    for weak_pw in ["123456", "password", "solident", "SOLIDENT123", "Solident"]:
        payload = {
            "username": f"user_{weak_pw}",
            "password": weak_pw,
            "dni": "87654321",
            "nombres": "Pedro",
            "apellidos": "Gomez",
            "telefono": "987654322",
            "correo": "pedro@example.com",
            "fecha_nacimiento": "1998-03-20",
        }
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_registro_paciente_password_valida_clinica2026(client):
    payload = {
        "username": "paciente_clinica",
        "password": "Clinica2026",
        "dni": "77889900",
        "nombres": "Ana",
        "apellidos": "Torres",
        "telefono": "987654323",
        "correo": "ana@example.com",
        "fecha_nacimiento": "1992-10-10",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["user"]["username"] == "paciente_clinica"

    # Verificar que puede iniciar sesión con la contraseña válida
    login_res = client.post(
        "/api/auth/login",
        json={"username": "paciente_clinica", "password": "Clinica2026"},
    )
    assert login_res.status_code == status.HTTP_200_OK
    assert "accessToken" in login_res.json()


def test_obtener_perfil_me(client, db_session):
    usuario = Usuario(
        username="testuser",
        password=get_password_hash("clave123"),
        activo=True,
        user_role=UserRoleEnum.PACIENTE,
        fecha_registro=datetime.now(timezone.utc),
    )

    db_session.add(usuario)
    db_session.commit()

    token = create_access_token(
        data={
            "sub": "testuser",
            "user_role": "PACIENTE",
        }
    )

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["username"] == "testuser"
    assert data["user_role"] == "PACIENTE"
    assert data["activo"] is True
