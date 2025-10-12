from io import BytesIO

from PIL import Image


def process_profile_image(image_data: bytes, max_size: int = 5 * 1024 * 1024) -> bytes:
    """プロフィール画像を圧縮・リサイズ (5MB以上はエラー)"""
    if len(image_data) > max_size:
        raise ValueError(f"画像サイズは{max_size // 1024 // 1024}MB以内にしてください")

    img = Image.open(BytesIO(image_data))
    img.thumbnail((200, 200), Image.Resampling.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="WEBP", quality=80, optimize=True)
    return buf.getvalue()
