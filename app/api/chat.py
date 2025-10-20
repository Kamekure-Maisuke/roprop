import json
from dataclasses import asdict, dataclass
from datetime import datetime
from uuid import UUID

from litestar import Request, Router, WebSocket, get, post, websocket
from litestar.exceptions import ValidationException

from app.auth import session_auth_guard
from app.redis_client import get_redis
from models import ChatMessage, ChatMessageTable, EmployeeTable


@dataclass
class SendMessageRequest:
    receiver_id: str
    content: str


@dataclass
class MessageResponse:
    id: str
    sender_id: str
    sender_name: str
    receiver_id: str
    receiver_name: str
    content: str
    created_at: str
    is_read: bool


@post("/messages")
async def send_message(data: SendMessageRequest, request: Request) -> dict[str, str]:
    """メッセージ送信"""
    sender_id = UUID(request.state.user_id)
    receiver_id = UUID(data.receiver_id)

    # 受信者が存在するかチェック
    if not await EmployeeTable.exists().where(EmployeeTable.id == receiver_id):
        raise ValidationException(detail="受信者が見つかりません")

    # メッセージをDBに保存
    message = ChatMessage(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=data.content,
        created_at=datetime.now(),
    )

    await ChatMessageTable.insert(
        ChatMessageTable(
            id=message.id,
            sender_id=message.sender_id,
            receiver_id=message.receiver_id,
            content=message.content,
            created_at=message.created_at,
            is_read=False,
        )
    )

    # Redisでリアルタイム配信
    redis = await get_redis()
    await redis.publish(f"chat:{receiver_id}", json.dumps(asdict(message), default=str))

    return {"message": "送信しました", "id": str(message.id)}


@get("/messages/{user_id:uuid}")
async def get_messages(user_id: UUID, request: Request) -> list[MessageResponse]:
    """特定ユーザーとのメッセージ履歴取得（最新200件）"""
    current_user_id = UUID(request.state.user_id)

    # 自分と相手のメッセージを最新200件取得
    messages = (
        await ChatMessageTable.select()
        .where(
            (
                (ChatMessageTable.sender_id == current_user_id)
                & (ChatMessageTable.receiver_id == user_id)
            )
            | (
                (ChatMessageTable.sender_id == user_id)
                & (ChatMessageTable.receiver_id == current_user_id)
            )
        )
        .order_by(ChatMessageTable.created_at, ascending=False)
        .limit(200)
    )
    messages = list(reversed(messages))

    # 2人の社員情報を一度だけ取得
    sender = (
        await EmployeeTable.select().where(EmployeeTable.id == current_user_id).first()
    )
    receiver = await EmployeeTable.select().where(EmployeeTable.id == user_id).first()

    sender_name = sender["name"] if sender else "Unknown"
    receiver_name = receiver["name"] if receiver else "Unknown"

    # メッセージをレスポンス形式に変換
    result = []
    for msg in messages:
        is_current_user_sender = msg["sender_id"] == current_user_id
        result.append(
            MessageResponse(
                id=str(msg["id"]),
                sender_id=str(msg["sender_id"]),
                sender_name=sender_name if is_current_user_sender else receiver_name,
                receiver_id=str(msg["receiver_id"]),
                receiver_name=receiver_name if is_current_user_sender else sender_name,
                content=msg["content"],
                created_at=msg["created_at"].isoformat(),
                is_read=msg["is_read"],
            )
        )

    return result


@get("/conversations")
async def get_conversations(request: Request) -> list[dict]:
    """会話一覧を取得"""
    current_user_id = UUID(request.state.user_id)

    # 最新メッセージと未読件数を1クエリで取得
    rows = await ChatMessageTable.raw(
        """
        WITH latest_messages AS (
            SELECT DISTINCT ON (
                CASE WHEN sender_id = {} THEN receiver_id ELSE sender_id END
            )
                CASE WHEN sender_id = {} THEN receiver_id ELSE sender_id END as other_user_id,
                content, created_at
            FROM chat_messages
            WHERE sender_id = {} OR receiver_id = {}
            ORDER BY CASE WHEN sender_id = {} THEN receiver_id ELSE sender_id END, created_at DESC
        ),
        unread_counts AS (
            SELECT sender_id, COUNT(*) as count
            FROM chat_messages
            WHERE receiver_id = {} AND is_read = FALSE
            GROUP BY sender_id
        )
        SELECT l.other_user_id, e.name, l.content, l.created_at, COALESCE(u.count, 0) as unread_count
        FROM latest_messages l
        LEFT JOIN employees e ON e.id = l.other_user_id
        LEFT JOIN unread_counts u ON u.sender_id = l.other_user_id
        ORDER BY l.created_at DESC
        """,
        current_user_id,
        current_user_id,
        current_user_id,
        current_user_id,
        current_user_id,
        current_user_id,
    )

    return [
        {
            "user_id": str(row["other_user_id"]),
            "user_name": row["name"] or "Unknown",
            "last_message": row["content"],
            "last_message_time": row["created_at"].isoformat(),
            "unread_count": row["unread_count"],
        }
        for row in rows
    ]


@post("/messages/{message_id:uuid}/read")
async def mark_as_read(message_id: UUID, request: Request) -> dict[str, str]:
    """メッセージを既読にする"""
    current_user_id = UUID(request.state.user_id)

    await ChatMessageTable.update({ChatMessageTable.is_read: True}).where(
        (ChatMessageTable.id == message_id)
        & (ChatMessageTable.receiver_id == current_user_id)
    )

    return {"message": "既読にしました"}


@get("/unread-counts")
async def get_unread_counts(request: Request) -> dict[str, int]:
    """全社員の未読件数を取得"""
    current_user_id = UUID(request.state.user_id)

    # 未読メッセージを取得
    unread_messages = await ChatMessageTable.select(ChatMessageTable.sender_id).where(
        (ChatMessageTable.receiver_id == current_user_id)
        & (ChatMessageTable.is_read == False)  # noqa: E712
    )

    # 送信者ごとにカウント
    counts = {}
    for msg in unread_messages:
        sender_id = str(msg["sender_id"])
        counts[sender_id] = counts.get(sender_id, 0) + 1

    return counts


@websocket("/ws")
async def chat_websocket(socket: WebSocket) -> None:
    """WebSocketでリアルタイムメッセージ受信"""
    await socket.accept()

    # セッションからユーザーIDを取得
    session_id = socket.cookies.get("session_id")
    if not session_id:
        await socket.close(code=4001, reason="認証が必要です")
        return

    from app.cache import get_cached

    session = await get_cached(f"session:{session_id}")
    if not session:
        await socket.close(code=4001, reason="セッションが無効です")
        return

    user_id = session["user_id"]
    redis = await get_redis()
    pubsub = redis.pubsub()

    # 自分宛のチャンネルを購読
    await pubsub.subscribe(f"chat:{user_id}")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                # メッセージをクライアントに送信
                data = json.loads(message["data"])
                await socket.send_json(data)
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe(f"chat:{user_id}")
        await pubsub.close()
        await socket.close()


chat_api_router = Router(
    path="/chat",
    route_handlers=[
        send_message,
        get_messages,
        get_conversations,
        mark_as_read,
        get_unread_counts,
        chat_websocket,
    ],
    guards=[session_auth_guard],
)
