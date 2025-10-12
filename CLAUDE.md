# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

Litestar(Python) + PostgreSQLを使用したPC・社員・部署管理アプリ。REST APIとHTMLフォームの両方でCRUD操作を提供。

リレーション: PC→社員(assigned_to)、社員→部署(department_id)、PC割り当て履歴(PCAssignmentHistory)

## コマンド

```bash
# データベース起動
docker compose up -d

# 開発サーバー起動
uv run uvicorn main:app --reload

# Lint/Format/テスト
uv run ruff check
uv run ruff format
uv run pytest
uv run pytest test_main.py::test_create_pc  # 単一テスト実行
```

APIドキュメント: http://localhost:8000/schema (ReDoc), http://localhost:8000/schema/swagger (Swagger)

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

**PC割り当て履歴**:
- PC作成/更新時に`assigned_to`が変更されたら、`PCAssignmentHistoryTable`に自動記録

**テンプレート**: Jinja2 (`templates/`ディレクトリ)、HTMLルートは`Template`または`Redirect`を返す
