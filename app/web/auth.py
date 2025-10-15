from litestar import Request, Router, get
from litestar.response import Redirect, Template

from app.cache import get_cached


@get("/auth/login")
async def show_login(request: Request) -> Template | Redirect:
    """ログイン画面"""
    if (session_id := request.cookies.get("session_id")) and await get_cached(
        f"session:{session_id}"
    ):
        return Redirect(path="/dashboard")
    return Template(template_name="login.html")


@get("/auth/verify")
async def show_verify_otp(email: str, request: Request) -> Template | Redirect:
    """OTP入力画面"""
    if (session_id := request.cookies.get("session_id")) and await get_cached(
        f"session:{session_id}"
    ):
        return Redirect(path="/dashboard")
    return Template(template_name="verify_otp.html", context={"email": email})


auth_web_router = Router(path="", route_handlers=[show_login, show_verify_otp])
