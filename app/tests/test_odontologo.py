
from datetime import datetime, time, timezone

from fastapi import status

from app.models.models import (
    Usuario,
    Odontologo,
    HorarioPersonal,
    UserRoleEnum,
    EspecialidadEnum,
    DiaSemanaEnum,
)
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


def crear_odontologo(
    db_session,
    dni="12345678",
    username="odontologo_test",
):
    usuario = Usuario(
        username=username,
        password=get_password_hash("clave123"),
        activo=True,
        user_role=UserRoleEnum.ODONTOLOGO,
        fecha_registro=datetime.now(timezone.utc),
    )

    odontologo = Odontologo(
        dni=dni,
        username=username,
        nombres="Carlos",
        apellidos="Ramirez",
        telefono=f"{int(dni):09d}",
        correo=f"{username}@example.com",
        activo=True,
        fecha_registro=datetime.now(timezone.utc),
        colegiatura=f"COP-{dni}",
        especialidad=EspecialidadEnum.ORTODONCIA,
    )

    db_session.add(usuario)
    db_session.add(odontologo)
    db_session.commit()

    return odontologo


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


def test_listar_especialidades(client, db_session):
    crear_usuario(db_session)

    response = client.get(
        "/api/odontologos/especialidades",
        headers=headers_token("admin_test", UserRoleEnum.SYSTEM_ADMIN),
    )

    assert response.status_code == status.HTTP_200_OK
    assert "ORTODONCIA" in response.json()
    assert "ENDODONCIA" in response.json()


def test_listar_odontologos_exitoso(client, db_session):
    crear_usuario(db_session)
    crear_odontologo(db_session)

    response = client.get(
        "/api/odontologos",
        headers=headers_token("admin_test", UserRoleEnum.SYSTEM_ADMIN),
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["dni"] == "12345678"


def test_obtener_mi_perfil_odontologo(client, db_session):
    crear_odontologo(db_session)

    response = client.get(
        "/api/odontologos/me",
        headers=headers_token("odontologo_test", UserRoleEnum.ODONTOLOGO),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "odontologo_test"


def test_obtener_odontologo_por_dni(client, db_session):
    crear_usuario(db_session)
    crear_odontologo(db_session)

    response = client.get(
        "/api/odontologos/12345678",
        headers=headers_token("admin_test", UserRoleEnum.SYSTEM_ADMIN),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["dni"] == "12345678"


def test_registrar_odontologo_exitoso(client, db_session):
    crear_usuario(db_session)

    payload = {
        "dni": "11223344",
        "username": "nuevo_odontologo",
        "password": "clave_segura123",
        "nombres": "Maria",
        "apellidos": "Lopez",
        "telefono": "912345678",
        "correo": "maria.odontologa@example.com",
        "colegiatura": "COP-11223344",
        "especialidad": "ORTODONCIA",
    }

    response = client.post(
        "/api/odontologos",
        json=payload,
        headers=headers_token("admin_test", UserRoleEnum.SYSTEM_ADMIN),
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["dni"] == "11223344"
    assert response.json()["username"] == "nuevo_odontologo"


def test_actualizar_odontologo_propio(client, db_session):
    crear_odontologo(db_session)

    response = client.put(
        "/api/odontologos/12345678",
        json={"nombres": "Carlos Alberto"},
        headers=headers_token("odontologo_test", UserRoleEnum.ODONTOLOGO),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["nombres"] == "Carlos Alberto"


def test_cambiar_estado_odontologo_como_administrador(client, db_session):
    crear_usuario(db_session)
    crear_odontologo(db_session)

    response = client.patch(
        "/api/odontologos/12345678/estado",
        params={"activo": "false"},
        headers=headers_token("admin_test", UserRoleEnum.SYSTEM_ADMIN),
    )

    assert response.status_code == status.HTTP_200_OK

    odontologo = db_session.query(Odontologo).filter_by(
        dni="12345678"
    ).first()

    assert odontologo.activo is False

    usuario = db_session.query(Usuario).filter_by(
        username="odontologo_test"
    ).first()

    assert usuario.activo is False


def test_listar_horarios_odontologo(client, db_session):
    crear_usuario(db_session)
    crear_odontologo(db_session)

    horario = HorarioPersonal(
        dni="12345678",
        dia_semana=DiaSemanaEnum.LUNES,
        hora_inicio=time(8, 0),
        hora_fin=time(17, 0),
    )

    db_session.add(horario)
    db_session.commit()

    response = client.get(
        "/api/odontologos/12345678/horarios",
        headers=headers_token("admin_test", UserRoleEnum.SYSTEM_ADMIN),
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["dia_semana"] == "LUNES"


def test_listar_horarios_odontologo_por_dia(client, db_session):
    crear_usuario(db_session)
    crear_odontologo(db_session)

    horario = HorarioPersonal(
        dni="12345678",
        dia_semana=DiaSemanaEnum.LUNES,
        hora_inicio=time(8, 0),
        hora_fin=time(17, 0),
    )

    db_session.add(horario)
    db_session.commit()

    response = client.get(
        "/api/odontologos/12345678/horarios/LUNES",
        headers=headers_token("admin_test", UserRoleEnum.SYSTEM_ADMIN),
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["dia_semana"] == "LUNES"


def test_paciente_no_puede_registrar_odontologo(client, db_session):
    crear_usuario(
        db_session,
        "paciente_test",
        UserRoleEnum.PACIENTE,
    )

    payload = {
        "dni": "11223344",
        "username": "nuevo_odontologo",
        "password": "clave123",
        "nombres": "Maria",
        "apellidos": "Lopez",
        "telefono": "912345678",
        "correo": "maria@example.com",
        "colegiatura": "COP-11223344",
        "especialidad": "ORTODONCIA",
    }

    response = client.post(
        "/api/odontologos",
        json=payload,
        headers=headers_token("paciente_test", UserRoleEnum.PACIENTE),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_odontologo_no_puede_cambiar_estado(client, db_session):
    crear_odontologo(db_session)

    response = client.patch(
        "/api/odontologos/12345678/estado",
        params={"activo": "false"},
        headers=headers_token("odontologo_test", UserRoleEnum.ODONTOLOGO),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_registrar_odontologo_con_dni_duplicado(client, db_session):
    crear_usuario(db_session)
    crear_odontologo(db_session)

    payload = {
        "dni": "12345678",
        "username": "otro_odontologo",
        "password": "clave123",
        "nombres": "Maria",
        "apellidos": "Lopez",
        "telefono": "912345678",
        "correo": "maria@example.com",
        "colegiatura": "COP-OTRO",
        "especialidad": "ORTODONCIA",
    }

    response = client.post(
        "/api/odontologos",
        json=payload,
        headers=headers_token("admin_test", UserRoleEnum.SYSTEM_ADMIN),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_obtener_odontologo_inexistente(client, db_session):
    crear_usuario(db_session)

    response = client.get(
        "/api/odontologos/99999999",
        headers=headers_token("admin_test", UserRoleEnum.SYSTEM_ADMIN),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_listar_horarios_con_dia_invalido(client, db_session):
    crear_usuario(db_session)
    crear_odontologo(db_session)

    response = client.get(
        "/api/odontologos/12345678/horarios/DIASINEXISTENTE",
        headers=headers_token("admin_test", UserRoleEnum.SYSTEM_ADMIN),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_odontologo_no_puede_modificar_su_colegiatura(client, db_session):
    odontologo = crear_odontologo(db_session)

    response = client.put(
        f"/api/odontologos/{odontologo.dni}",
        json={"colegiatura": "COP-99999"},
        headers=headers_token(
            odontologo.username,
            UserRoleEnum.ODONTOLOGO,
        ),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_odontologo_no_puede_modificar_su_especialidad(client, db_session):
    odontologo = crear_odontologo(db_session)

    response = client.put(
        f"/api/odontologos/{odontologo.dni}",
        json={"especialidad": "ENDODONCIA"},
        headers=headers_token(
            odontologo.username,
            UserRoleEnum.ODONTOLOGO,
        ),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
