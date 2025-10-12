import base64

from litestar.testing import TestClient

from main import create_app


def test_web_basic_auth_required():
    """WebルートはBasic認証が必要"""
    with TestClient(app=create_app()) as client:
        response = client.get("/dashboard")
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers


def test_web_basic_auth_failure():
    """誤った認証情報はリジェクトされる"""
    with TestClient(app=create_app()) as client:
        credentials = base64.b64encode(b"xxxuser:xxxpass").decode("utf-8")
        response = client.get(
            "/dashboard", headers={"Authorization": f"Basic {credentials}"}
        )
        assert response.status_code == 401
