from typing import TypedDict, cast

import httpx


class DepartmentDict(TypedDict):
    name: str


class DepartmentResponse(TypedDict):
    id: str
    name: str


BASE_URL = "http://localhost:8000"

departments: list[DepartmentDict] = [
    {"name": "開発部"},
    {"name": "営業部"},
    {"name": "デザイン部"},
    {"name": "総務部"},
    {"name": "品質管理部"},
]

with httpx.Client() as client:
    for department in departments:
        response = client.post(f"{BASE_URL}/departments", json=department)
        if response.status_code == 201:
            data = cast(DepartmentResponse, response.json())
            print(f"✓ {department['name']} を登録しました (ID: {data['id']})")
        else:
            print(
                f"✗ {department['name']} の登録に失敗しました: {response.status_code}"
            )

print(f"\n{len(departments)}件の部署登録が完了しました")
