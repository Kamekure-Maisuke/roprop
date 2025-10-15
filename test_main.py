from unittest.mock import patch

from litestar.testing import TestClient

from main import create_app


def test_api_bearer_auth_required():
    """API認証が必須であることの確認"""
    with TestClient(app=create_app()) as client:
        assert client.get("/pcs").status_code == 401
        assert client.get("/employees").status_code == 401
        assert client.get("/departments").status_code == 401


@patch("app.auth.API_TOKEN", "test-token")
def test_api_invalid_bearer_token():
    """不正なトークンは401を返す"""
    with TestClient(app=create_app()) as client:
        res = client.get("/pcs", headers={"Authorization": "Bearer wrong-token"})
        assert res.status_code == 401


@patch("app.auth.API_TOKEN", "test-token")
def test_api_valid_bearer_token():
    """正しいトークンで認証成功"""
    with TestClient(app=create_app()) as client:
        res = client.get("/pcs", headers={"Authorization": "Bearer test-token"})
        assert res.status_code == 200
