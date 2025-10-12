import base64
import json
from unittest.mock import AsyncMock, patch

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
@patch("app.cache.redis")
def test_api_valid_bearer_token(mock_redis):
    """正しいトークンで認証成功"""
    mock_redis.get = AsyncMock(return_value=json.dumps([]))
    mock_redis.setex = AsyncMock()
    with TestClient(app=create_app()) as client:
        res = client.get("/pcs", headers={"Authorization": "Bearer test-token"})
        assert res.status_code == 200


def test_web_basic_auth_required():
    """WebルートはBasic認証が必要"""
    with TestClient(app=create_app()) as client:
        response = client.get("/dashboard")
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers


def test_web_basic_auth_failure():
    """誤ったBasic認証情報は401を返す。"""
    with TestClient(app=create_app()) as client:
        credentials = base64.b64encode(b"xxxuser:xxxpass").decode("utf-8")
        response = client.get(
            "/dashboard", headers={"Authorization": f"Basic {credentials}"}
        )
        assert response.status_code == 401


@patch("app.auth.WEB_BASIC_USERNAME", "testname")
@patch("app.auth.WEB_BASIC_PASSWORD", "testpass")
def test_web_basic_auth_success():
    """正しいBasic情報で認証成功"""
    with patch("app.web.dashboard.get_cached") as mock_cache:
        mock_cache.return_value = {
            "dept_stats": [],
            "unassigned_pc_count": 0,
            "total_pcs": 0,
            "total_employees": 0,
            "total_departments": 0,
        }
        with TestClient(app=create_app()) as client:
            credentials = base64.b64encode(b"testname:testpass").decode("utf-8")
            response = client.get(
                "/dashboard", headers={"Authorization": f"Basic {credentials}"}
            )
            assert response.status_code == 200