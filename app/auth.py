import os
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from litestar.handlers.base import BaseRouteHandler

from app.cache import get_cached, redis
from models import Role

API_TOKEN = os.getenv("API_TOKEN", "")


async def bearer_token_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Bearer Token認証ガード(API用)"""
    auth_header = connection.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise NotAuthorizedException(detail="Missing or invalid Authorization header")
    if auth_header[7:] != API_TOKEN:
        raise NotAuthorizedException(detail="Invalid token")


class SessionExpiredException(PermissionDeniedException):
    """セッション切れ例外"""

    status_code = 401


async def session_auth_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """セッション認証ガード(Web UI用)"""
    if not (session_id := connection.cookies.get("session_id")):
        raise SessionExpiredException(detail="ログインが必要です")

    if not (session_data := await get_cached(f"session:{session_id}")):
        raise SessionExpiredException(detail="セッションが無効です")

    connection.state.user_id = session_data["user_id"]
    connection.state.email = session_data["email"]
    connection.state.role = Role(session_data.get("role", Role.USER.value))
    await redis.expire(f"session:{session_id}", 86400)


async def admin_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """管理者権限ガード"""
    await session_auth_guard(connection, _)
    if connection.state.role != Role.ADMIN:
        raise PermissionDeniedException(detail="管理者権限が必要です")
