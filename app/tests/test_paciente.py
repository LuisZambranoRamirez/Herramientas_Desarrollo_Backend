
from datetime import date, datetime, timezone

from fastapi import status

from app.models.models import Usuario, Paciente, UserRoleEnum
from app.core.security import get_password_hash, create_access_token


def crear_usuario(
    db_session,
    username="admin_test",
    role=UserRoleEnum.SYSTEM_ADMIN,
):
    usuario = Usuario(
        username=username,
        password=get_password_hash("clave123"),
        activo=True,
        user_role=role,
        fecha_registro=datetime.now(timezone.utc),
    )

    db_session.add(usuario)
    db_session.commit()

    return usuario


def crear_paciente(
    db_session,
    dni="12345678",
    username="paciente_test",
):
    usuario = Usuario(
        username=username,
        password=get_password_hash("clave123"),
        activo=True,
        user_role=UserRoleEnum.PACIENTE,
        fecha_registro=datetime.now(timezone.utc),
    )

    paciente = Paciente(
        dni=dni,
        username=username,
        nombres="Juan",
        apellidos="Perez",
        telefono=f"{int(dni[-9:]):09d}",
        correo=f"{username}@example.com",
        direccion=f"Direccion {dni}",
        observaciones="Paciente de prueba",
        fecha_nacimiento=date(2000, 5, 15),
        fecha_registro=datetime.now(timezone.utc),
    )

    db_session.add(usuario)
    db_session.add(paciente)
    db_session.commit()

    return paciente


def obtener_token(username, role):
    return create_access_token(
        data={
            "sub": username,
            "user_role": role.value,
        }
    )


def headers_token(username, role):
    token = obtener_token(username, role)

    return {
        "Authorization": f"Bearer {token}"
    }


def test_listar_pacientes_exitoso(client, db_session):
    crear_usuario(db_session)
    crear_paciente(db_session)

    response = client.get(
        "/api/pacientes",
        headers=headers_token(
            "admin_test",
            UserRoleEnum.SYSTEM_ADMIN
        ),
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["dni"] == "12345678"


def test_listar_pacientes_sin_permisos(client, db_session):
    crear_paciente(db_session)

    response = client.get(
        "/api/pacientes",
        headers=headers_token(
            "paciente_test",
            UserRoleEnum.PACIENTE
        ),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_obtener_paciente_por_dni(client, db_session):
    crear_paciente(db_session)

    response = client.get(
        "/api/pacientes/12345678",
        headers=headers_token(
            "paciente_test",
            UserRoleEnum.PACIENTE
        ),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["dni"] == "12345678"
    assert response.json()["nombres"] == "Juan"


def test_paciente_no_puede_consultar_otro_paciente(client, db_session):
    crear_paciente(
        db_session,
        "12345678",
        "paciente_uno"
    )

    crear_paciente(
        db_session,
        "87654321",
        "paciente_dos"
    )

    response = client.get(
        "/api/pacientes/87654321",
        headers=headers_token(
            "paciente_uno",
            UserRoleEnum.PACIENTE
        ),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_obtener_mi_perfil_paciente(client, db_session):
    crear_paciente(db_session)

    response = client.get(
        "/api/pacientes/me",
        headers=headers_token(
            "paciente_test",
            UserRoleEnum.PACIENTE
        ),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "paciente_test"


def test_registrar_paciente_exitoso(client, db_session):
    crear_usuario(db_session)

    payload = {
        "dni": "11223344",
        "username": "nuevo_paciente",
        "password": "clave_segura123",
        "nombres": "Maria",
        "apellidos": "Lopez",
        "telefono": "912345678",
        "correo": "maria@example.com",
        "direccion": "Av. Prueba 100",
        "observaciones": "Registro de prueba",
        "fecha_nacimiento": "1998-08-20",
    }

    response = client.post(
        "/api/pacientes",
        json=payload,
        headers=headers_token(
            "admin_test",
            UserRoleEnum.SYSTEM_ADMIN
        ),
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["dni"] == "11223344"
    assert response.json()["username"] == "nuevo_paciente"


def test_actualizar_paciente_propio(client, db_session):
    crear_paciente(db_session)

    response = client.put(
        "/api/pacientes/12345678",
        json={
            "nombres": "Juan Carlos"
        },
        headers=headers_token(
            "paciente_test",
            UserRoleEnum.PACIENTE
        ),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["nombres"] == "Juan Carlos"


def test_desactivar_paciente_como_administrador(client, db_session):
    crear_usuario(db_session)
    crear_paciente(db_session)

    response = client.delete(
        "/api/pacientes/12345678",
        headers=headers_token(
            "admin_test",
            UserRoleEnum.SYSTEM_ADMIN
        ),
    )

    assert response.status_code == status.HTTP_200_OK

    assert "desactivado exitosamente" in response.json()["message"]

    usuario = db_session.query(Usuario).filter_by(
        username="paciente_test"
    ).first()

    assert usuario.activo is False
