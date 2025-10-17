# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 応答形式
- シンプルな回答
- 結果はシンプルに。過程やまとめは端的に技術的知見を分かりやすく回答。
- 世界的なエンジニア(ケントンプソンやロブパイク等)になりきって回答。

## コード生成規約
- 最も短く美しいロジックでPythonの標準的な記法に沿った可読性の高いコードで書く。
- LitestarやPiccolo ORMを便利に活用。
- Unix哲学に従う。

## プロジェクト概要

Litestar(Python) + PostgreSQLを使用したPC・社員・部署管理アプリ。REST APIとHTMLフォームの両方でCRUD操作を提供。

リレーション: PC→社員(assigned_to)、社員→部署(department_id)、PC割り当て履歴(PCAssignmentHistory)

## コマンド
- README.mdを参照

## アーキテクチャ

**ディレクトリ構成**:
```
app/
  api/         - REST APIエンドポイント (pcs.py, employees.py, departments.py)
  web/         - HTMLフォームルート (pcs.py, employees.py, departments.py, dashboard.py)
  database.py  - Piccolo用エンジン設定
  config.py    - データベース接続設定
models.py      - Piccolo ORMモデル (*Model) とdataclass (*) を定義
main.py        - アプリ起動エントリーポイント (create_app)
init_data/pg/  - PostgreSQL初期化SQLスクリプト (Docker起動時に自動実行)
templates/     - Jinja2テンプレート
```

**データモデル**:
- `models.py`には2種類の定義が共存
  - Piccolo ORMモデル: `DepartmentTable`, `EmployeeTable`, `PCTable`, `PCAssignmentHistoryTable`
  - Dataclassモデル (API入出力用): `Department`, `Employee`, `PC`, `PCAssignmentHistory`

**ルート構成**:
- REST API: `/pcs`, `/employees`, `/departments` (POST/GET/PUT/DELETE)
- PC履歴: `GET /pcs/{pc_id}/history` (API), `GET /history` (全履歴)
- HTML: `/{resource}/view`, `/{resource}/register`, `/{resource}/{id}/edit`, `/{resource}/{id}/delete`
- ダッシュボード: `GET /dashboard` - 部署別統計表示

**データベース**:
- PostgreSQL 18 (Docker Compose)
- ポート: 5430 (ホスト) -> 5432 (コンテナ)
- Piccolo ORMでアクセス