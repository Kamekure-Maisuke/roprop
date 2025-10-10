# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

Litestar(Python Webフレームワーク)を使用したPC管理アプリケーションです。PCレコードのCRUD操作を行うためのREST APIエンドポイントとHTMLベースのWebインターフェースの両方を提供します。データは一旦ディクショナリを使用してメモリ内に保存されます。

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

## アーキテクチャ

### アプリケーション構造

アプリケーションは3つのメインファイルに分かれています:

1. **models.py**: `PC`データクラスを定義(フィールド: id(UUID), name, model, serial_number, assigned_to)
2. **main.py**: すべてのルートハンドラとアプリケーション設定
3. **test_main.py**: pytestフィクスチャを使用した包括的なテストスイート

### ルート構成

アプリケーションは2つの並行したインターフェースを持ちます:

**REST APIエンドポイント** (`/pcs`):
- `POST /pcs` - PC作成(201を返す)
- `GET /pcs` - 全PC一覧取得
- `GET /pcs/{pc_id}` - 特定PC取得
- `PUT /pcs/{pc_id}` - PC更新
- `DELETE /pcs/{pc_id}` - PC削除(204を返す)

**HTMLフォームベースエンドポイント**:
- `GET /pcs/view` - 全PCをHTMLテーブルで表示
- `GET /pcs/register` + `POST /pcs/register` - 登録フォーム
- `GET /pcs/{pc_id}/edit` + `POST /pcs/{pc_id}/edit` - 編集フォーム
- `POST /pcs/{pc_id}/delete` - フォーム経由で削除

### データストレージ

PCはモジュールレベルのディクショナリに保存されます: `pcs: dict[UUID, PC] = {}`。これはインメモリのみでサーバー再起動時にリセットされます。テストスイートは`autouse=True`のpytestフィクスチャを使用して各テストの前後でこのディクショナリをクリアします。

### テンプレートシステム

`templates/`ディレクトリに保存されたJinja2テンプレート(`JinjaTemplateEngine`経由)を使用します。HTMLルートは`Template`オブジェクトまたは`Redirect`レスポンスを返します。

### アプリケーションファクトリ

`create_app()`関数は設定済みのLitestarインスタンスを返します。すべてのルートハンドラは`route_handlers`パラメータに明示的にリストされています。

## CI/CD

GitHub Actions CIはmain以外のすべてのブランチで実行されます:
- Lintジョブ: `basedpyright`を実行
- Testジョブ: `pytest`を実行

両方のジョブはキャッシュを有効にした`uv`を依存関係管理に使用します。
