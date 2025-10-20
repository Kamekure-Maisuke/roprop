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


@patch("app.auth.API_TOKEN", "test-token")
def test_create_and_get_pc():
    """PCの作成と取得"""
    from uuid import uuid4

    with TestClient(app=create_app()) as client:
        pc_id = uuid4()
        pc_data = {
            "id": str(pc_id),
            "name": "TestPC-001",
            "model": "MacBook Pro",
            "serial_number": "SN123456",
            "assigned_to": None,
        }

        # 作成
        res = client.post(
            "/pcs",
            json=pc_data,
            headers={"Authorization": "Bearer test-token"},
        )
        assert res.status_code == 201
        assert res.json()["name"] == "TestPC-001"
        assert res.json()["model"] == "MacBook Pro"

        # 削除
        res = client.get(
            f"/pcs/{pc_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert res.status_code == 200
        assert res.json()["serial_number"] == "SN123456"


@patch("app.auth.API_TOKEN", "test-token")
def test_update_and_delete_pc():
    """PCの更新と削除"""
    from uuid import uuid4

    with TestClient(app=create_app()) as client:
        pc_id = uuid4()
        pc_data = {
            "id": str(pc_id),
            "name": "TestPC-002",
            "model": "ThinkPad X1",
            "serial_number": "SN789012",
            "assigned_to": None,
        }

        # 作成
        client.post(
            "/pcs",
            json=pc_data,
            headers={"Authorization": "Bearer test-token"},
        )

        # 更新
        pc_data["name"] = "TestPC-002-Updated"
        res = client.put(
            f"/pcs/{pc_id}",
            json=pc_data,
            headers={"Authorization": "Bearer test-token"},
        )
        assert res.status_code == 200
        assert res.json()["name"] == "TestPC-002-Updated"

        # 削除
        res = client.delete(
            f"/pcs/{pc_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert res.status_code == 204

        # 削除確認
        res = client.get(
            f"/pcs/{pc_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert res.status_code == 404
