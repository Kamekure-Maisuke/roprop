import httpx

BASE_URL = "http://localhost:8000"

employees = [
    {
        "name": "山田太郎",
        "email": "yamada.taro@example.com",
        "department": "開発部",
    },
    {
        "name": "佐藤花子",
        "email": "sato.hanako@example.com",
        "department": "開発部",
    },
    {
        "name": "鈴木一郎",
        "email": "suzuki.ichiro@example.com",
        "department": "開発部",
    },
    {
        "name": "田中美咲",
        "email": "tanaka.misaki@example.com",
        "department": "開発部",
    },
    {
        "name": "伊藤健太",
        "email": "ito.kenta@example.com",
        "department": "開発部",
    },
    {
        "name": "渡辺明",
        "email": "watanabe.akira@example.com",
        "department": "営業部",
    },
    {
        "name": "高橋さくら",
        "email": "takahashi.sakura@example.com",
        "department": "営業部",
    },
    {
        "name": "小林大輔",
        "email": "kobayashi.daisuke@example.com",
        "department": "営業部",
    },
    {
        "name": "加藤美優",
        "email": "kato.miyu@example.com",
        "department": "営業部",
    },
    {
        "name": "山本翔太",
        "email": "yamamoto.shota@example.com",
        "department": "営業部",
    },
    {
        "name": "中村愛",
        "email": "nakamura.ai@example.com",
        "department": "デザイン部",
    },
    {
        "name": "吉田優斗",
        "email": "yoshida.yuto@example.com",
        "department": "デザイン部",
    },
    {
        "name": "清水結衣",
        "email": "shimizu.yui@example.com",
        "department": "デザイン部",
    },
    {
        "name": "森本拓海",
        "email": "morimoto.takumi@example.com",
        "department": "総務部",
    },
    {
        "name": "林千尋",
        "email": "hayashi.chihiro@example.com",
        "department": "総務部",
    },
    {
        "name": "松本蓮",
        "email": "matsumoto.ren@example.com",
        "department": "品質管理部",
    },
    {
        "name": "木村陽菜",
        "email": "kimura.hina@example.com",
        "department": "品質管理部",
    },
]

with httpx.Client() as client:
    for employee in employees:
        response = client.post(f"{BASE_URL}/employees", json=employee)
        if response.status_code == 201:
            print(f"✓ {employee['name']} ({employee['department']}) を登録しました")
        else:
            print(f"✗ {employee['name']} の登録に失敗しました: {response.status_code}")

print(f"\n{len(employees)}件の社員登録が完了しました")
