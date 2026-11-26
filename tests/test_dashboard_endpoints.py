import os

os.environ.setdefault("DATABASE_URL", "postgresql://usuario:clave@localhost:5432/prueba")
os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas")

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.dashboard import DashboardResumenResponse
from app.services.dashboard import obtener_resumen


@pytest.fixture
def cliente_como():
    def crear(rol):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        if rol is not None:
            app.dependency_overrides[get_current_user] = lambda: MagicMock(
                username="usuario", user_role=rol
            )
        return TestClient(app)

    yield crear
    app.dependency_overrides.clear()


def test_resumen_sin_token_responde_401(cliente_como):
    cliente = cliente_como(None)

    respuesta = cliente.get("/api/dashboard/resumen")

    assert respuesta.status_code == 401


@pytest.mark.parametrize("rol", ["PACIENTE", "ODONTOLOGO"])
def test_resumen_rechaza_roles_que_no_son_admin(cliente_como, rol):
    cliente = cliente_como(rol)

    respuesta = cliente.get("/api/dashboard/resumen")

    assert respuesta.status_code == 403


@patch("app.routers.dashboard.dashboard_service.obtener_resumen")
def test_resumen_admin_devuelve_los_cuatro_totales(mock_servicio, cliente_como):
    mock_servicio.return_value = DashboardResumenResponse(
        citas_hoy=5,
        pacientes_total=40,
        tratamientos_en_proceso=7,
        insumos_stock_bajo=2,
    )
    cliente = cliente_como("SYSTEM_ADMIN")

    respuesta = cliente.get("/api/dashboard/resumen")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "citas_hoy": 5,
        "pacientes_total": 40,
        "tratamientos_en_proceso": 7,
        "insumos_stock_bajo": 2,
    }


def test_servicio_rechaza_usuario_que_no_es_admin():
    usuario = MagicMock(user_role="PACIENTE")

    with pytest.raises(HTTPException) as error:
        obtener_resumen(MagicMock(), usuario)

    assert error.value.status_code == 403