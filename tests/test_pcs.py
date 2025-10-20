"""PC API のCRUD操作テスト"""

from uuid import uuid4


def test_create_and_get_pc(auth_client, auth_headers):
    """PCの作成と取得"""
    pc_id = uuid4()
    pc_data = {
        "id": str(pc_id),
        "name": "TestPC-001",
        "model": "MacBook Pro",
        "serial_number": "SN123456",
        "assigned_to": None,
    }

    # 作成
    res = auth_client.post("/pcs", json=pc_data, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["name"] == "TestPC-001"
    assert res.json()["model"] == "MacBook Pro"

    # 取得
    res = auth_client.get(f"/pcs/{pc_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["serial_number"] == "SN123456"


def test_update_and_delete_pc(auth_client, auth_headers):
    """PCの更新と削除"""
    pc_id = uuid4()
    pc_data = {
        "id": str(pc_id),
        "name": "TestPC-002",
        "model": "ThinkPad X1",
        "serial_number": "SN789012",
        "assigned_to": None,
    }

    # 作成
    auth_client.post("/pcs", json=pc_data, headers=auth_headers)

    # 更新
    pc_data["name"] = "TestPC-002-Updated"
    res = auth_client.put(f"/pcs/{pc_id}", json=pc_data, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "TestPC-002-Updated"

    # 削除
    res = auth_client.delete(f"/pcs/{pc_id}", headers=auth_headers)
    assert res.status_code == 204

    # 削除確認
    res = auth_client.get(f"/pcs/{pc_id}", headers=auth_headers)
    assert res.status_code == 404
