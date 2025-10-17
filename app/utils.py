import logging
import os
import random
import smtplib
from email.mime.text import MIMEText
from io import BytesIO

from PIL import Image

from app.config import SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER

logger = logging.getLogger(__name__)


def process_profile_image(image_data: bytes, max_size: int = 5 * 1024 * 1024) -> bytes:
    """プロフィール画像を圧縮・リサイズ (5MB以上はエラー)"""
    if len(image_data) > max_size:
        raise ValueError(f"画像サイズは{max_size // 1024 // 1024}MB以内にしてください")

    img = Image.open(BytesIO(image_data))
    img.thumbnail((200, 200), Image.Resampling.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="WEBP", quality=80, optimize=True)
    return buf.getvalue()


def generate_random_pc_name() -> str:
    """ランダムなPC名を生成 (形容詞-名詞-数字 形式)"""
    adjectives = [
        "swift",
        "brave",
        "silent",
        "mighty",
        "bright",
        "cosmic",
        "cyber",
        "quantum",
        "turbo",
        "ultra",
        "golden",
        "silver",
        "steel",
        "thunder",
        "rapid",
        "smart",
        "cool",
        "sharp",
        "wild",
        "grand",
        "neon",
        "shadow",
        "crimson",
        "azure",
        "omega",
        "alpha",
        "delta",
        "gamma",
        "stellar",
        "lunar",
        "solar",
        "nova",
        "frost",
        "blaze",
        "storm",
        "volt",
        "hydro",
        "aero",
        "geo",
        "chrono",
    ]
    nouns = [
        "hawk",
        "dragon",
        "phoenix",
        "tiger",
        "wolf",
        "falcon",
        "eagle",
        "panther",
        "shark",
        "bear",
        "viper",
        "cobra",
        "leopard",
        "lynx",
        "fox",
        "raven",
        "lion",
        "jaguar",
        "kraken",
        "sphinx",
        "titan",
        "knight",
        "samurai",
        "ninja",
        "wizard",
        "archer",
        "hunter",
        "rider",
        "warrior",
        "guardian",
        "specter",
        "daemon",
        "wraith",
        "golem",
        "titan",
        "oracle",
        "nexus",
        "core",
        "vector",
    ]
    num = random.randint(100, 999)
    return f"{random.choice(adjectives)}-{random.choice(nouns)}-{num}"


async def send_otp_email(to: str, otp: str) -> None:
    """OTPをメール送信"""
    # 開発環境ではログに出力
    if os.getenv("ENV") == "development" or not SMTP_USER:
        logger.info("=" * 50)
        logger.info("📧 [開発環境] メール送信")
        logger.info("=" * 50)
        logger.info(f"宛先: {to}")
        logger.info("件名: ログインコード")
        logger.info(f"ログインコード: {otp}")
        logger.info("10分間有効です。")
        logger.info("=" * 50)
        return

    msg = MIMEText(f"ログインコード: {otp}\n\n10分間有効です。")
    msg["Subject"] = "ログインコード"
    msg["From"] = SMTP_USER
    msg["To"] = to

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
