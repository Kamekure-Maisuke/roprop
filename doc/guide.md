
## ルーティング

### HTTP メソッドデコレータ
- **`@get`, `@post`, `@put`, `@delete`**: RESTful APIエンドポイント定義
  - パスパラメータ: `{pc_id:uuid}` でUUID型を自動パース・バリデーション

```python
from litestar import get, post, put, delete
from uuid import UUID

@get("/pcs")
async def list_pcs() -> list[PC]:
    return await P.select()

@get("/pcs/{pc_id:uuid}")
async def get_pc(pc_id: UUID) -> PC:
    # pc_idは自動的にUUID型に変換
    return await P.select().where(P.id == pc_id).first()

@post("/pcs", status_code=201)
async def create_pc(data: PC) -> PC:
    await P(**data.__dict__).save()
    return data

@put("/pcs/{pc_id:uuid}")
async def update_pc(pc_id: UUID, data: PC) -> PC:
    await P.update({...}).where(P.id == pc_id)
    return data

@delete("/pcs/{pc_id:uuid}", status_code=204)
async def delete_pc(pc_id: UUID) -> None:
    await P.delete().where(P.id == pc_id)
```

### Router
- **`Router(path, route_handlers, guards, security)`**: エンドポイントをグループ化

```python
from litestar import Router
from app.auth import bearer_token_guard

pc_api_router = Router(
    path="",
    route_handlers=[
        list_pcs,
        get_pc,
        create_pc,
        update_pc,
        delete_pc,
    ],
    guards=[bearer_token_guard],  # 全エンドポイントに認証適用
    security=[{"BearerAuth": []}],  # OpenAPI用セキュリティ定義
)
```

## レスポンス

### Template
- **`Template(template_name, context)`**: Jinja2テンプレートレンダリング
  - Webフォーム表示・一覧画面で活用

```python
from litestar import get
from litestar.response import Template

@get("/pcs/view")
async def view_pcs(page: int = 1) -> Template:
    pcs = await P.select().limit(10).offset((page - 1) * 10)
    return Template(
        template_name="pc_list.html",
        context={"pcs": pcs, "page": page}
    )
```

### Redirect
- **`Redirect(path)`**: リダイレクト応答
  - フォーム送信後やセッション切れ時に使用

```python
from litestar import post
from litestar.response import Redirect

@post("/pcs/{pc_id:uuid}/edit")
async def edit_pc(pc_id: UUID, data: FormData) -> Redirect:
    await P.update({...}).where(P.id == pc_id)
    return Redirect(path="/pcs/view")

# 例外ハンドラーでの使用
def session_expired_handler(request: Request, exc: SessionExpiredException) -> Redirect:
    return Redirect(path="/auth/login")
```

### Response
- **`Response(content, status_code, media_type, headers)`**: カスタムレスポンス
  - TSVエクスポートや一括削除API等に利用。

```python
from litestar import get
from litestar.response import Response
from datetime import datetime

@get("/pcs/export")
async def export_pcs_tsv() -> Response:
    pcs = await P.select()
    tsv_content = "\n".join([f"{p.id}\t{p.name}" for p in pcs])
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

    return Response(
        content=tsv_content.encode("utf-8"),
        media_type="text/tab-separated-values; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="pcs_{timestamp}.tsv"'
        },
    )
```

## 認証・認可

### Guards
- **`bearer_token_guard`**: Bearer Token認証(API用)
- **`session_auth_guard`**: セッション認証(Web UI用)
  - 二段キャッシュ(メモリ→Redis)で高速化
  - `connection.state`にユーザー情報格納

- **`admin_guard`**: 管理者権限チェック
  - `session_auth_guard`を内部で呼び出し

```python
from litestar.connection import ASGIConnection
from litestar.handlers.base import BaseRouteHandler
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException

# Bearer Token認証(API用)
async def bearer_token_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    auth_header = connection.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise NotAuthorizedException(detail="Missing Authorization header")
    if auth_header[7:] != API_TOKEN:
        raise NotAuthorizedException(detail="Invalid token")

# セッション認証(Web UI用)
async def session_auth_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    session_id = connection.cookies.get("session_id")
    if not session_id:
        raise PermissionDeniedException(detail="ログインが必要です")

    session_data = await get_cached(f"session:{session_id}")
    if not session_data:
        raise PermissionDeniedException(detail="セッションが無効です")

    # ユーザー情報を connection.state に格納
    connection.state.user_id = session_data["user_id"]
    connection.state.role = Role(session_data["role"])

# 管理者権限チェック
async def admin_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    await session_auth_guard(connection, _)  # セッション認証を実行
    if connection.state.role != Role.ADMIN:
        raise PermissionDeniedException(detail="管理者権限が必要です")

# ルートハンドラーでの使用
@get("/pcs/register", guards=[admin_guard])
async def show_register_form() -> Template:
    return Template("pc_register.html")
```

### 例外ハンドリング
- **`exception_handlers`**: カスタム例外処理
  - `SessionExpiredException` → ログインページへ自動リダイレクト

```python
from litestar import Litestar, Request
from litestar.response import Redirect

class SessionExpiredException(PermissionDeniedException):
    status_code = 401

def session_expired_handler(request: Request, exc: SessionExpiredException) -> Redirect:
    return Redirect(path="/auth/login")

app = Litestar(
    route_handlers=[...],
    exception_handlers={SessionExpiredException: session_expired_handler},
)
```

## リクエスト処理

### パラメータ注入
- **`Request.state`**: ガードで設定したユーザー情報取得
- **`Body(media_type=RequestEncodingType.URL_ENCODED)`**: フォームデータパース
- **パスパラメータ**: `{pc_id:uuid}` でUUID自動変換
- **クエリパラメータ**: `page: int = 1` でデフォルト値指定

```python
from litestar import Request, get, post
from litestar.params import Body
from litestar.enums import RequestEncodingType
from typing import Annotated

# Request.state でユーザー情報取得
@get("/pcs/view")
async def view_pcs(request: Request, page: int = 1) -> Template:
    user_id = request.state.user_id  # guardで設定された値
    role = request.state.role
    return Template("pc_list.html", {"user_id": user_id, "role": role})

# HTMLフォームデータパース
FormData = Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)]

@post("/pcs/register")
async def register_pc(data: FormData) -> Template:
    # data = {"name": "...", "model": "...", "serial_number": "..."}
    pc = PC(name=data["name"], model=data["model"])
    await P(**pc.__dict__).save()
    return Template("pc_register.html", {"success": True})

# パスパラメータ自動変換
@get("/pcs/{pc_id:uuid}")
async def get_pc(pc_id: UUID) -> PC:  # pc_id は自動的に UUID 型
    return await P.select().where(P.id == pc_id).first()

# クエリパラメータ(デフォルト値指定)
@get("/history/view")
async def view_history(page: int = 1, limit: int = 10) -> Template:
    offset = (page - 1) * limit
    histories = await H.select().limit(limit).offset(offset)
    return Template("history.html", {"histories": histories})
```

### バリデーション
- **Pydantic連携**: dataclassで自動バリデーション
  - `ValidationException`で不正リクエスト拒否

```python
from dataclasses import dataclass
from litestar import post
from litestar.exceptions import ValidationException

@dataclass
class CreatePCRequest:
    name: str
    model: str
    serial_number: str  # 必須フィールド

@post("/pcs")
async def create_pc(data: CreatePCRequest) -> PC:
    # dataclassの型チェックが自動実行される
    # serial_number が空の場合は ValidationException が発生
    await P(**data.__dict__).save()
    return data
```

## データベース連携

### Piccolo ORM統合
- **非同期クエリ**: `await Table.select()`, `await Table.insert()`

- **SQLインジェクション対策**: Piccoloのパラメータ化クエリ

## ページネーション

### ClassicPagination
- **`ClassicPagination(items, page_size, current_page, total_pages)`**: ページング機能

```python
from litestar import get
from litestar.pagination import ClassicPagination

@get("/pcs/view")
async def view_pcs(page: int = 1) -> Template:
    page_size = 10
    total = await P.count()
    pcs = await P.select().limit(page_size).offset((page - 1) * page_size)

    pagination = ClassicPagination(
        items=pcs,
        page_size=page_size,
        current_page=page,
        total_pages=(total + page_size - 1) // page_size,
    )

    return Template("pc_list.html", {"pagination": pagination})
```

## WebSocket

### @websocket
- **`@websocket(path)`**: リアルタイム双方向通信
  - Redis Pub/Subと組み合わせてチャット機能実装
  - `socket.accept()`, `socket.send_json()`, `socket.close()`

```python
from litestar import websocket, WebSocket
from litestar.exceptions import WebSocketDisconnect
import json

@websocket("/ws")
async def chat_websocket(socket: WebSocket) -> None:
    await socket.accept()

    # セッション認証
    session_id = socket.cookies.get("session_id")
    if not session_id:
        await socket.close(code=4001, reason="認証が必要です")
        return

    session = await get_cached(f"session:{session_id}")
    user_id = session["user_id"]

    # Redis Pub/Sub購読
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"chat:{user_id}")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await socket.send_json(data)  # クライアントに送信
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"chat:{user_id}")
        await socket.close()
```

## OpenAPI

### OpenAPIConfig
- **`OpenAPIConfig(title, version, components)`**: Swagger UI自動生成
  - Bearer認証スキーマ定義(`BearerAuth`)
- **`security`**: エンドポイント単位でセキュリティ要件指定

```python
from litestar import Litestar
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Components, SecurityScheme

app = Litestar(
    route_handlers=[...],
    openapi_config=OpenAPIConfig(
        title="PC管理API",
        version="1.0.0",
        components=Components(
            security_schemes={
                "BearerAuth": SecurityScheme(
                    type="http",
                    scheme="bearer",
                    bearer_format="JWT",
                    description="APIトークンを入力してください",
                )
            }
        ),
    ),
)
# /schema/swagger でSwagger UI が自動生成される
```

## テンプレートエンジン

### TemplateConfig
- **`TemplateConfig(directory, engine)`**: Jinja2設定

```python
from pathlib import Path
from litestar import Litestar
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig

app = Litestar(
    route_handlers=[...],
    template_config=TemplateConfig(
        directory=Path("templates"),
        engine=JinjaTemplateEngine,
    ),
)
```

## プラグイン

### GranianPlugin
- **`GranianPlugin()`**: 高速ASGIサーバー統合

```python
from litestar import Litestar
from litestar_granian import GranianPlugin

app = Litestar(
    plugins=[GranianPlugin()],
    route_handlers=[...],
)
# uvicornより高速なGranianサーバーで起動
```

## ステータスコード

### カスタムステータス
- **`status_code`パラメータ**: レスポンスコード明示
  - `HTTP_201_CREATED` - リソース作成
  - `HTTP_204_NO_CONTENT` - 削除成功

```python
from litestar import post, delete
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT

@post("/pcs", status_code=HTTP_201_CREATED)
async def create_pc(data: PC) -> PC:
    await P(**data.__dict__).save()
    return data  # 201 Created

@delete("/pcs/{pc_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_pc(pc_id: UUID) -> None:
    await P.delete().where(P.id == pc_id)
    # 204 No Content (レスポンスボディなし)
```

## キャッシュ活用

### Redis連携(Litestar非依存)
- **クエリキャッシュ**: `get_cached`, `set_cached`, `delete_cached`
  - TTL指定でキャッシュ有効期限管理

- **セッション管理**: 二段キャッシュ(メモリ→Redis)
  - 頻繁なセッション確認を高速化

## 使い所まとめ

| 機能 | 用途 | ファイル例 |
|------|------|-----------|
| `@get/@post/@put/@delete` | REST API定義 | `app/api/*.py` |
| `Template` | HTML画面表示 | `app/web/*.py` |
| `Redirect` | フォーム送信後の遷移 | `app/web/pcs.py:220` |
| `guards` | 認証・認可 | `app/auth.py` |
| `exception_handlers` | エラー時の自動処理 | `main.py:60` |
| `ClassicPagination` | 大量データの分割表示 | `app/web/pcs.py:109` |
| `@websocket` | リアルタイム通信 | `app/api/chat.py:206` |
| `OpenAPIConfig` | API仕様書自動生成 | `main.py:65` |

## 推奨パターン

### API or Web UI
- **API**: `Router` + `guards=[bearer_token_guard]` + dataclass
- **Web UI**: `Router` + `guards=[session_auth_guard]` + `Template` + `FormData`

### セキュリティ層
1. `bearer_token_guard`: APIトークンチェック
2. `session_auth_guard`: セッションチェック + ユーザー情報取得
3. `admin_guard`: 管理者権限チェック

### レスポンス選択
- データ取得 → dataclass(自動JSON変換)
- 画面表示 → `Template`
- 遷移 → `Redirect`
- ファイルDL → `Response` + カスタムヘッダー
