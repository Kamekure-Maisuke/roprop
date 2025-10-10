# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

Litestar(Python)を使用したPC・社員・部署管理アプリ。REST APIとHTMLフォームの両方でCRUD操作を提供。データはインメモリ(再起動でリセット)。

リレーション: PC→社員(assigned_to)、社員→部署(department_id)、PC割り当て履歴(PCAssignmentHistory)

## コマンド

```bash
# 開発サーバー
uv run uvicorn main:app --reload

# Lint/テスト
uv run basedpyright
uv run pytest
uv run pytest test_main.py::test_create_pc

# 開発データ投入(順序重要)
uv run seeder/departments.py
uv run seeder/employees.py
uv run seeder/pcs.py
```

APIドキュメント: http://localhost:8000/schema

## アーキテクチャ

**ファイル構成**:
- `models.py`: `Employee`, `PC`, `Department`, `PCAssignmentHistory`
- `main.py`: 全ルートハンドラ + `create_app()`
- `test_main.py`: `autouse=True`フィクスチャでストレージをクリア
- `seeder/`: 開発データ投入スクリプト

**主要ルート**:
- REST API: `/pcs`, `/employees`, `/departments` (POST/GET/PUT/DELETE)
- PC履歴: `GET /pcs/{pc_id}/history` (API), `/pcs/{pc_id}/history/view` (HTML)
- ダッシュボード: `GET /dashboard` - 部署別統計表示
- HTML: `/{resource}/view`, `/{resource}/register`, `/{resource}/{id}/edit`, `/{resource}/{id}/delete`

**データストレージ** (main.py内のモジュールレベルdict):
```python
pcs: dict[UUID, PC] = {}
employees: dict[UUID, Employee] = {}
departments: dict[UUID, Department] = {}
pc_assignment_histories: dict[UUID, PCAssignmentHistory] = {}
```

**PC割り当て履歴**: PC作成/更新時に`assigned_to`が変更されたら自動記録

**テンプレート**: Jinja2 (`templates/`ディレクトリ)、HTMLルートは`Template`または`Redirect`を返す
