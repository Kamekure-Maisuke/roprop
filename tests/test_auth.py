"""認証機能のテスト"""


def test_api_bearer_auth_required(client):
    """API認証が必須であることの確認"""
    assert client.get("/pcs").status_code == 401
    assert client.get("/employees").status_code == 401
    assert client.get("/departments").status_code == 401


def test_api_invalid_bearer_token(auth_client):
    """不正なトークンは401を返す"""
    res = auth_client.get("/pcs", headers={"Authorization": "Bearer wrong-token"})
    assert res.status_code == 401


def test_api_valid_bearer_token(auth_client, auth_headers):
    """正しいトークンで認証成功"""
    res = auth_client.get("/pcs", headers=auth_headers)
    assert res.status_code == 200
