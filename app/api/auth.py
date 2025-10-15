import secrets
from dataclasses import dataclass
from datetime import datetime

from litestar import Request, Response, Router, post
from litestar.exceptions import NotAuthorizedException, TooManyRequestsException

from app.cache import delete_cached, get_cached, redis, set_cached
from app.utils import send_otp_email
from models import EmployeeTable


@dataclass
class SendOTPRequest:
    email: str


@dataclass
class VerifyOTPRequest:
    email: str
    otp: str


async def check_rate_limit(key: str, max: int, window: int) -> None:
    """レート制限チェック"""
    if (count := await redis.get(key)) and int(count) >= max:
        raise TooManyRequestsException(detail="試行回数の上限に達しました")
    await redis.incr(key)
    await redis.expire(key, window)


@post("/send-otp")
async def send_otp(data: SendOTPRequest) -> dict[str, str]:
    """OTP送信"""
    await check_rate_limit(f"rate:otp:{data.email}", 5, 300)
    if (
        not await EmployeeTable.select()
        .where(EmployeeTable.email == data.email)
        .first()
    ):
        raise NotAuthorizedException(detail="メールアドレスが登録されていません")

    otp = "".join(str(secrets.randbelow(10)) for _ in range(6))
    await set_cached(f"otp:{data.email}", {"code": otp, "attempts": 0}, 600)
    await send_otp_email(data.email, otp)
    return {"message": "OTPを送信しました"}


@post("/verify-otp")
async def verify_otp(data: VerifyOTPRequest) -> Response[dict[str, str]]:
    """OTP検証&ログイン"""
    await check_rate_limit(f"rate:login:{data.email}", 10, 600)

    if not (otp_data := await get_cached(f"otp:{data.email}")):
        raise NotAuthorizedException(detail="OTPが無効または期限切れです")

    if otp_data["attempts"] >= 5:
        await delete_cached(f"otp:{data.email}")
        raise NotAuthorizedException(detail="試行回数超過")

    if not secrets.compare_digest(data.otp, otp_data["code"]):
        otp_data["attempts"] += 1
        await set_cached(f"otp:{data.email}", otp_data, 600)
        raise NotAuthorizedException(detail="OTPが正しくありません")

    employee = (
        await EmployeeTable.select().where(EmployeeTable.email == data.email).first()
    )
    session_id = secrets.token_urlsafe(32)
    await set_cached(
        f"session:{session_id}",
        {
            "user_id": str(employee["id"]),
            "email": data.email,
            "created_at": datetime.now().isoformat(),
        },
        86400,
    )
    await delete_cached(f"otp:{data.email}")

    response = Response({"message": "ログイン成功"})
    response.set_cookie(
        "session_id", session_id, httponly=True, max_age=86400, samesite="strict"
    )
    return response


@post("/logout")
async def logout(request: Request) -> Response[dict[str, str]]:
    """ログアウト"""
    if session_id := request.cookies.get("session_id"):
        await delete_cached(f"session:{session_id}")
    response = Response({"message": "ログアウトしました"})
    response.delete_cookie("session_id")
    return response


auth_router = Router(path="/auth", route_handlers=[send_otp, verify_otp, logout])
