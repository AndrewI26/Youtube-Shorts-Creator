from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

FRONTEND = "http://localhost:3000"


def preflight(client, origin):
    return client.options(
        "/shorts/create/",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )


def test_preflight_from_frontend_is_allowed(client):
    response = preflight(client, FRONTEND)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] in ("*", FRONTEND)
    assert "POST" in response.headers["access-control-allow-methods"]


def test_simple_request_has_cors_header(client):
    response = client.get("/shorts/", headers={"Origin": FRONTEND})
    assert response.headers["access-control-allow-origin"] == "*"


def test_restricted_origins(settings):
    app = create_app(Settings(**{**settings.__dict__, "cors_origins": [FRONTEND]}))
    with TestClient(app) as client:
        assert preflight(client, FRONTEND).headers["access-control-allow-origin"] == FRONTEND
        blocked = preflight(client, "http://evil.example")
        assert blocked.status_code == 400
        assert "access-control-allow-origin" not in blocked.headers
