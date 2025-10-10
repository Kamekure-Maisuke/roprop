# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

Litestar(Python Webフレームワーク)を使用したPC・社員管理アプリケーションです。PC及び社員(Employee)レコードのCRUD操作を行うためのREST APIエンドポイントとHTMLベースのWebインターフェースの両方を提供します。PCは社員に割り当てることができます。データはディクショナリを使用してメモリ内に保存されます(サーバー再起動時にリセット)。

## コマンド

### 開発サーバー実行
```bash
uv run uvicorn main:app --reload
```

### 型チェック(Lint)
```bash
uv run basedpyright
```

### テスト
```bash
# 全テスト実行
uv run pytest

# 特定のテスト実行
uv run pytest test_main.py::test_create_pc
```

### APIドキュメント
- ReDoc: http://localhost:8000/schema
- Swagger UI: http://localhost:8000/schema/swagger

### 開発用データ投入
```bash
# サーバーを起動してから別ターミナルで実行
# 1. 先に社員データを投入
uv run seeder/employees.py

# 2. 次にPCデータを投入(社員に割り当てるため)
uv run seeder/pcs.py
```

## アーキテクチャ

### アプリケーション構造

アプリケーションは以下のファイルで構成されています:

1. **models.py**: データモデル定義
   - `Employee`: 社員情報(id, name, email, department)
   - `PC`: PC情報(id, name, model, serial_number, assigned_to)
2. **main.py**: すべてのルートハンドラとアプリケーション設定
3. **test_main.py**: pytestフィクスチャを使用した包括的なテストスイート
4. **seeder/**: 開発用データ投入スクリプト
   - `employees.py`: 17名の社員データを投入
   - `pcs.py`: 20台のPCデータを投入(一部は社員に割り当て済み)

### ルート構成

アプリケーションは2つの並行したインターフェースを持ちます:

**REST APIエンドポイント**:

PC管理:
- `POST /pcs` - PC作成(201を返す)
- `GET /pcs` - 全PC一覧取得
- `GET /pcs/{pc_id}` - 特定PC取得
- `PUT /pcs/{pc_id}` - PC更新
- `DELETE /pcs/{pc_id}` - PC削除(204を返す)

社員管理:
- `POST /employees` - 社員作成(201を返す)
- `GET /employees` - 全社員一覧取得
- `GET /employees/{employee_id}` - 特定社員取得
- `PUT /employees/{employee_id}` - 社員更新
- `DELETE /employees/{employee_id}` - 社員削除(204を返す)

**HTMLフォームベースエンドポイント**:

PC管理:
- `GET /pcs/view` - 全PCをHTMLテーブルで表示
- `GET /pcs/register` + `POST /pcs/register` - 登録フォーム
- `GET /pcs/{pc_id}/edit` + `POST /pcs/{pc_id}/edit` - 編集フォーム
- `POST /pcs/{pc_id}/delete` - フォーム経由で削除

社員管理:
- `GET /employees/view` - 全社員をHTMLテーブルで表示
- `GET /employees/register` + `POST /employees/register` - 登録フォーム
- `GET /employees/{employee_id}/edit` + `POST /employees/{employee_id}/edit` - 編集フォーム
- `POST /employees/{employee_id}/delete` - フォーム経由で削除

### データストレージ

データはモジュールレベルのディクショナリに保存されます:
- `pcs: dict[UUID, PC] = {}`
- `employees: dict[UUID, Employee] = {}`

これらはインメモリのみでサーバー再起動時にリセットされます。テストスイートは`autouse=True`のpytestフィクスチャを使用して各テストの前後でこれらのディクショナリをクリアします。

PCの`assigned_to`フィールドは`Employee`のUUID(またはNone)を保持し、PC-社員間の関係を表現します。

### テンプレートシステム

`templates/`ディレクトリに保存されたJinja2テンプレート(`JinjaTemplateEngine`経由)を使用します。HTMLルートは`Template`オブジェクトまたは`Redirect`レスポンスを返します。

### アプリケーションファクトリ

`create_app()`関数は設定済みのLitestarインスタンスを返します。すべてのルートハンドラは`route_handlers`パラメータに明示的にリストされています。

## CI/CD

GitHub Actions CIはmain以外のすべてのブランチで実行されます:
- Lintジョブ: `basedpyright`を実行
- Testジョブ: `pytest`を実行

両方のジョブはキャッシュを有効にした`uv`を依存関係管理に使用します。
