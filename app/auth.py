import base64
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler

from app.config import API_TOKEN, WEB_BASIC_PASSWORD, WEB_BASIC_USERNAME


async def bearer_token_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Bearer Token認証ガード"""
    auth_header = connection.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise NotAuthorizedException(detail="Missing or invalid Authorization header")

    token = auth_header[7:]  # "Bearer "の後のトークン部分
    if token != API_TOKEN:
        raise NotAuthorizedException(detail="Invalid token")


async def basic_auth_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Basic認証ガード"""
    auth_header = connection.headers.get("Authorization", "")
    if not auth_header.startswith("Basic "):
        raise NotAuthorizedException(
            detail="Unauthorized",
            headers={"WWW-Authenticate": 'Basic realm="Web UI"'},
        )

    try:
        credentials = base64.b64decode(auth_header[6:]).decode("utf-8")
        username, password = credentials.split(":", 1)
    except Exception:
        raise NotAuthorizedException(
            detail="Invalid credentials format",
            headers={"WWW-Authenticate": 'Basic realm="Web UI"'},
        )

    if username != WEB_BASIC_USERNAME or password != WEB_BASIC_PASSWORD:
        raise NotAuthorizedException(
            detail="Invalid credentials",
            headers={"WWW-Authenticate": 'Basic realm="Web UI"'},
        )
