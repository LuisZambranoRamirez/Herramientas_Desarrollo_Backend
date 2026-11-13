import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_db, get_current_user


# =====================================================
# FIXTURES
# =====================================================

@pytest.fixture
def usuario_admin():
    return MagicMock(
        username="admin",
        user_role="ADMIN"
    )


@pytest.fixture
def usuario_paciente():
    return MagicMock(
        username="paciente1",
        user_role="PACIENTE"
    )


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def client(db, usuario_admin):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: usuario_admin

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def cita_response():
    return {
        "cita_id": "cita-001",
        "dni_paciente": "12345678",
        "dni_odontologo": "87654321",
        "fecha": "2026-11-10",
        "hora": "10:30:00",
        "motivo_consulta": "Dolor dental",
        "diagnostico": None,
        "estado": "PROGRAMADA",
        "fecha_registro": "2026-11-06T10:00:00",
        "paciente": {
            "dni": "12345678",
            "nombres": "Juan",
            "apellidos": "Perez",
            "telefono": "999999999",
            "correo": "juan@gmail.com"
        },
        "odontologo": {
            "dni": "87654321",
            "nombres": "Carlos",
            "apellidos": "Lopez",
            "especialidad": "ORTODONCIA",
            "colegiatura": "COP123"
        }
    }


# =====================================================
# LISTAR ODONTOLOGOS DISPONIBLES
# =====================================================

@patch("app.routers.cita.listar_odontologos_disponibles")
def test_endpoint_listar_odontologos(mock_service, client):
    mock_service.return_value = [
        {
            "dni": "87654321",
            "nombres": "Carlos",
            "apellidos": "Lopez",
            "especialidad": "ORTODONCIA",
            "colegiatura": "COP123"
        }
    ]

    response = client.get("/citas/odontologos-disponibles")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["dni"] == "87654321"


@patch("app.routers.cita.listar_odontologos_disponibles")
def test_endpoint_odontologos_vacio(mock_service, client):
    mock_service.return_value = []

    response = client.get("/citas/odontologos-disponibles")

    assert response.status_code == 200
    assert response.json() == []


# =====================================================
# AGENDAR CITA
# =====================================================

@patch("app.routers.cita.agendar_cita")
def test_endpoint_agendar_cita(
    mock_service, client, cita_response
):
    mock_service.return_value = cita_response

    payload = {
        "dni_odontologo": "87654321",
        "fecha": "2026-11-20",
        "hora": "10:30:00",
        "motivo_consulta": "Dolor dental",
        "diagnostico": None
    }

    response = client.post("/citas/", json=payload)

    assert response.status_code in (200, 201)
    assert response.json()["cita_id"] == "cita-001"

    mock_service.assert_called_once()


@patch("app.routers.cita.agendar_cita")
def test_endpoint_agendar_cita_conflicto(
    mock_service, client
):
    from fastapi import HTTPException

    mock_service.side_effect = HTTPException(
        status_code=409,
        detail="El odontólogo ya tiene una cita programada para esa fecha y hora"
    )

    payload = {
        "dni_odontologo": "87654321",
        "fecha": "2026-11-20",
        "hora": "10:30:00",
        "motivo_consulta": "Dolor dental"
    }

    response = client.post("/citas/", json=payload)

    assert response.status_code == 409


# =====================================================
# LISTAR MIS CITAS
# =====================================================

@patch("app.routers.cita.listar_mis_citas")
def test_endpoint_listar_mis_citas(
    mock_service, client, cita_response
):
    mock_service.return_value = [cita_response]

    response = client.get("/citas/mis-citas")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["cita_id"] == "cita-001"


@patch("app.routers.cita.listar_mis_citas")
def test_endpoint_mis_citas_vacio(mock_service, client):
    mock_service.return_value = []

    response = client.get("/citas/mis-citas")

    assert response.status_code == 200
    assert response.json() == []


# =====================================================
# LISTAR CITAS CON FILTROS
# =====================================================

@patch("app.routers.cita.listar_citas")
def test_endpoint_listar_citas(
    mock_service, client, cita_response
):
    mock_service.return_value = [cita_response]

    response = client.get("/citas/")

    assert response.status_code == 200
    assert len(response.json()) == 1


@patch("app.routers.cita.listar_citas")
def test_endpoint_listar_citas_con_filtros(
    mock_service, client, cita_response
):
    mock_service.return_value = [cita_response]

    response = client.get(
        "/citas/",
        params={
            "fecha": "2026-11-10",
            "estado": "PROGRAMADA",
            "dni_paciente": "12345678",
            "dni_odontologo": "87654321"
        }
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


@patch("app.routers.cita.listar_citas")
def test_endpoint_listar_citas_vacio(mock_service, client):
    mock_service.return_value = []

    response = client.get("/citas/")

    assert response.status_code == 200
    assert response.json() == []


# =====================================================
# OBTENER DETALLE DE CITA
# =====================================================

@patch("app.routers.cita.obtener_detalle_cita")
def test_endpoint_detalle_cita(
    mock_service, client, cita_response
):
    mock_service.return_value = cita_response

    response = client.get("/citas/cita-001")

    assert response.status_code == 200
    assert response.json()["cita_id"] == "cita-001"


@patch("app.routers.cita.obtener_detalle_cita")
def test_endpoint_detalle_cita_no_existe(
    mock_service, client
):
    from fastapi import HTTPException

    mock_service.side_effect = HTTPException(
        status_code=404,
        detail="Cita no encontrada"
    )

    response = client.get("/citas/inexistente")

    assert response.status_code == 404


# =====================================================
# ACTUALIZAR ESTADO
# =====================================================

@patch("app.routers.cita.actualizar_estado_cita")
def test_endpoint_actualizar_estado(
    mock_service, client, cita_response
):
    cita_response["estado"] = "ATENDIDA"
    mock_service.return_value = cita_response

    payload = {
        "estado": "ATENDIDA",
        "diagnostico": "Caries dental"
    }

    response = client.patch(
        "/citas/cita-001/estado",
        json=payload
    )

    assert response.status_code == 200
    assert response.json()["estado"] == "ATENDIDA"


@patch("app.routers.cita.actualizar_estado_cita")
def test_endpoint_estado_invalido(mock_service, client):
    from fastapi import HTTPException

    mock_service.side_effect = HTTPException(
        status_code=400,
        detail="Estado inválido"
    )

    response = client.patch(
        "/citas/cita-001/estado",
        json={"estado": "INVALIDO"}
    )

    assert response.status_code == 400


# =====================================================
# CANCELAR CITA
# =====================================================

@patch("app.routers.cita.cancelar_cita")
def test_endpoint_cancelar_cita(
    mock_service, client, cita_response
):
    cita_response["estado"] = "CANCELADA"
    mock_service.return_value = cita_response

    response = client.patch("/citas/cita-001/cancelar")

    assert response.status_code == 200
    assert response.json()["estado"] == "CANCELADA"


@patch("app.routers.cita.cancelar_cita")
def test_endpoint_cancelar_cita_no_existe(
    mock_service, client
):
    from fastapi import HTTPException

    mock_service.side_effect = HTTPException(
        status_code=404,
        detail="Cita no encontrada"
    )

    response = client.patch("/citas/inexistente/cancelar")

    assert response.status_code == 404


# =====================================================
# ACTUALIZAR / REPROGRAMAR CITA
# =====================================================

@patch("app.routers.cita.actualizar_cita")
def test_endpoint_actualizar_cita(
    mock_service, client, cita_response
):
    cita_response["fecha"] = "2026-11-15"
    cita_response["hora"] = "11:30:00"
    mock_service.return_value = cita_response

    payload = {
        "fecha": "2026-11-15",
        "hora": "11:30:00",
        "motivo_consulta": "Limpieza dental"
    }

    response = client.put(
        "/citas/cita-001",
        json=payload
    )

    assert response.status_code == 200
    assert response.json()["fecha"] == "2026-11-15"


@patch("app.routers.cita.actualizar_cita")
def test_endpoint_actualizar_cita_conflicto(
    mock_service, client
):
    from fastapi import HTTPException

    mock_service.side_effect = HTTPException(
        status_code=409,
        detail="El odontólogo ya tiene una cita programada para esa fecha y hora"
    )

    payload = {
        "fecha": "2026-11-15",
        "hora": "11:30:00"
    }

    response = client.put(
        "/citas/cita-001",
        json=payload
    )

    assert response.status_code == 409