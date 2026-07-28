from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

client = TestClient(app)


def test_api_rejects_missing_or_invalid_admin_token() -> None:
    settings = get_settings()
    original = settings.admin_api_token
    settings.admin_api_token = "correct-token"
    try:
        assert client.get("/api/languages").status_code == 401
        assert client.get("/api/languages", headers={"X-Admin-Token": "wrong"}).status_code == 401
    finally:
        settings.admin_api_token = original


def test_api_accepts_valid_admin_token() -> None:
    settings = get_settings()
    original = settings.admin_api_token
    settings.admin_api_token = "correct-token"
    try:
        response = client.get("/api/languages", headers={"X-Admin-Token": "correct-token"})
        assert response.status_code == 200
    finally:
        settings.admin_api_token = original


def test_api_fails_closed_when_admin_token_is_unset() -> None:
    settings = get_settings()
    original = settings.admin_api_token
    settings.admin_api_token = ""
    try:
        response = client.get("/api/languages")
        assert response.status_code == 503
        assert response.json()["detail"] == "ADMIN_API_TOKEN is not configured"
    finally:
        settings.admin_api_token = original


def test_health_endpoint_remains_public() -> None:
    assert client.get("/health/live").status_code == 200
