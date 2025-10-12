from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler

from app.config import API_TOKEN


async def bearer_token_guard(
    connection: ASGIConnection, _: BaseRouteHandler
) -> None:
    """Bearer Token認証ガード"""
    auth_header = connection.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise NotAuthorizedException(detail="Missing or invalid Authorization header")

    token = auth_header[7:]  # "Bearer "の後のトークン部分
    if token != API_TOKEN:
        raise NotAuthorizedException(detail="Invalid token")
