from datetime import datetime
from uuid import UUID, uuid4

from litestar import Request, Router, delete, post
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.auth import bearer_token_guard
from models import BlogLikeTable as BLT
from models import BlogPostTable as BPT


async def _check_post_exists(blog_post_id: UUID) -> None:
    """ブログ投稿が存在するか確認"""
    if not await BPT.exists().where(BPT.id == blog_post_id):
        raise NotFoundException(detail=f"Blog post with ID {blog_post_id} not found")


@post("/blogs/{blog_post_id:uuid}/like", status_code=HTTP_201_CREATED)
async def like_blog_post(blog_post_id: UUID, request: Request) -> dict:
    """ブログにいいねを追加"""
    await _check_post_exists(blog_post_id)
    employee_id = request.user.id

    # 既にいいね済みか確認
    if await BLT.exists().where(
        (BLT.blog_post_id == blog_post_id) & (BLT.employee_id == employee_id)
    ):
        return {
            "message": "Already liked this blog post",
            "like_count": await BLT.count().where(BLT.blog_post_id == blog_post_id),
        }

    # いいね追加
    await BLT(
        id=uuid4(),
        blog_post_id=blog_post_id,
        employee_id=employee_id,
        created_at=datetime.now(),
    ).save()

    # いいね数を取得
    like_count = await BLT.count().where(BLT.blog_post_id == blog_post_id)
    return {"message": "Liked successfully", "like_count": like_count}


@delete("/blogs/{blog_post_id:uuid}/like", status_code=HTTP_204_NO_CONTENT)
async def unlike_blog_post(blog_post_id: UUID, request: Request) -> None:
    """ブログのいいねを削除"""
    await _check_post_exists(blog_post_id)
    employee_id = request.user.id

    # いいね削除
    deleted = await BLT.delete().where(
        (BLT.blog_post_id == blog_post_id) & (BLT.employee_id == employee_id)
    )
    if not deleted:
        raise NotFoundException(detail="Like not found")


blog_like_api_router = Router(
    path="",
    route_handlers=[like_blog_post, unlike_blog_post],
    guards=[bearer_token_guard],
    security=[{"BearerAuth": []}],
)
