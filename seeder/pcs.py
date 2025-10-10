from typing import TypedDict, cast

import httpx


class EmployeeDict(TypedDict):
    id: str
    name: str
    email: str
    department_id: str | None


BASE_URL = "http://localhost:8000"

with httpx.Client() as client:
    response = client.get(f"{BASE_URL}/employees")
    if response.status_code != 200:
        print(
            "エラー: 社員データを取得できませんでした。先に employees.py を実行してください。"
        )
        exit(1)

    employees = cast(list[EmployeeDict], response.json())
    employee_map = {emp["name"]: emp["id"] for emp in employees}

pcs = [
    {
        "name": "開発用PC-01",
        "model": "ThinkPad X1 Carbon",
        "serial_number": "SN001234",
        "assigned_to": employee_map.get("山田太郎"),
    },
    {
        "name": "開発用PC-02",
        "model": "MacBook Pro 14",
        "serial_number": "SN001235",
        "assigned_to": employee_map.get("佐藤花子"),
    },
    {
        "name": "開発用PC-03",
        "model": "Dell XPS 13",
        "serial_number": "SN001236",
        "assigned_to": employee_map.get("鈴木一郎"),
    },
    {
        "name": "開発用PC-04",
        "model": "Surface Laptop 5",
        "serial_number": "SN001237",
        "assigned_to": employee_map.get("田中美咲"),
    },
    {
        "name": "開発用PC-05",
        "model": "ThinkPad T14",
        "serial_number": "SN001238",
        "assigned_to": employee_map.get("伊藤健太"),
    },
    {
        "name": "営業用PC-01",
        "model": "HP ProBook 450",
        "serial_number": "SN002001",
        "assigned_to": employee_map.get("渡辺明"),
    },
    {
        "name": "営業用PC-02",
        "model": "VAIO SX14",
        "serial_number": "SN002002",
        "assigned_to": employee_map.get("高橋さくら"),
    },
    {
        "name": "営業用PC-03",
        "model": "dynabook G83",
        "serial_number": "SN002003",
        "assigned_to": employee_map.get("小林大輔"),
    },
    {
        "name": "営業用PC-04",
        "model": "Lenovo V15",
        "serial_number": "SN002004",
        "assigned_to": employee_map.get("加藤美優"),
    },
    {
        "name": "営業用PC-05",
        "model": "FMV LIFEBOOK",
        "serial_number": "SN002005",
        "assigned_to": employee_map.get("山本翔太"),
    },
    {
        "name": "デザイン用PC-01",
        "model": "MacBook Pro 16",
        "serial_number": "SN003001",
        "assigned_to": employee_map.get("中村愛"),
    },
    {
        "name": "デザイン用PC-02",
        "model": "iMac 24",
        "serial_number": "SN003002",
        "assigned_to": employee_map.get("吉田優斗"),
    },
    {
        "name": "デザイン用PC-03",
        "model": "Surface Studio 2",
        "serial_number": "SN003003",
        "assigned_to": employee_map.get("清水結衣"),
    },
    {
        "name": "管理用PC-01",
        "model": "ThinkCentre M75s",
        "serial_number": "SN004001",
        "assigned_to": employee_map.get("森本拓海"),
    },
    {
        "name": "管理用PC-02",
        "model": "OptiPlex 3090",
        "serial_number": "SN004002",
        "assigned_to": employee_map.get("林千尋"),
    },
    {
        "name": "テスト用PC-01",
        "model": "ASUS VivoBook",
        "serial_number": "SN005001",
        "assigned_to": employee_map.get("松本蓮"),
    },
    {
        "name": "テスト用PC-02",
        "model": "Acer Aspire 5",
        "serial_number": "SN005002",
        "assigned_to": employee_map.get("木村陽菜"),
    },
    {
        "name": "予備PC-01",
        "model": "HP 255 G8",
        "serial_number": "SN006001",
        "assigned_to": None,
    },
    {
        "name": "予備PC-02",
        "model": "Lenovo IdeaPad",
        "serial_number": "SN006002",
        "assigned_to": None,
    },
    {
        "name": "会議室PC",
        "model": "NUC 11",
        "serial_number": "SN007001",
        "assigned_to": None,
    },
]

with httpx.Client() as client:
    for pc in pcs:
        response = client.post(f"{BASE_URL}/pcs", json=pc)
        if response.status_code == 201:
            print(f"✓ {pc['name']} を登録しました")
        else:
            print(f"✗ {pc['name']} の登録に失敗しました: {response.status_code}")

print(f"\n{len(pcs)}件のPC登録が完了しました")
