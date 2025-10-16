from uuid import UUID

from litestar import Request, Router, get
from litestar.response import Template

from app.auth import session_auth_guard
from models import ChatMessageTable, EmployeeTable


@get("/chat")
async def view_chat(request: Request) -> Template:
    """チャット画面"""
    current_user_id = UUID(request.state.user_id)
    employees = await EmployeeTable.select().order_by(EmployeeTable.name)

    # 各社員の未読件数を取得
    unread_counts = {}
    for emp in employees:
        count = await ChatMessageTable.count().where(
            (ChatMessageTable.sender_id == emp["id"])
            & (ChatMessageTable.receiver_id == current_user_id)
            & (ChatMessageTable.is_read == False)  # noqa: E712
        )
        unread_counts[str(emp["id"])] = count

    return Template(
        template_name="chat.html",
        context={
            "employees": employees,
            "current_user_id": str(current_user_id),
            "unread_counts": unread_counts,
        },
    )


@get("/chat/{user_id:uuid}")
async def view_chat_with_user(user_id: UUID, request: Request) -> Template:
    """特定ユーザーとのチャット画面"""
    current_user_id = UUID(request.state.user_id)
    employees = await EmployeeTable.select().order_by(EmployeeTable.name)
    selected_user = (
        await EmployeeTable.select().where(EmployeeTable.id == user_id).first()
    )

    # 各社員の未読件数を取得
    unread_counts = {}
    for emp in employees:
        count = await ChatMessageTable.count().where(
            (ChatMessageTable.sender_id == emp["id"])
            & (ChatMessageTable.receiver_id == current_user_id)
            & (ChatMessageTable.is_read == False)  # noqa: E712
        )
        unread_counts[str(emp["id"])] = count

    # 選択中ユーザーのメッセージを既読にする
    await ChatMessageTable.update({ChatMessageTable.is_read: True}).where(
        (ChatMessageTable.sender_id == user_id)
        & (ChatMessageTable.receiver_id == current_user_id)
    )

    return Template(
        template_name="chat.html",
        context={
            "employees": employees,
            "selected_user": selected_user,
            "current_user_id": str(current_user_id),
            "unread_counts": unread_counts,
        },
    )


chat_web_router = Router(
    path="",
    route_handlers=[view_chat, view_chat_with_user],
    guards=[session_auth_guard],
)
