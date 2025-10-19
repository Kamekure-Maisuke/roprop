from datetime import datetime
from typing import Annotated
from uuid import UUID

from litestar import Request, Router, get, post
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.pagination import ClassicPagination
from litestar.params import Body
from litestar.response import Redirect, Template

from app.auth import session_auth_guard
from app.cache import delete_cached
from models import (
    BlogLikeTable as BLT,
    BlogPost,
    BlogPostTable as B,
    BlogPostTagTable as BPT,
    Employee,
    EmployeeTable as E,
    Tag,
    TagTable as T,
)

FormData = Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)]


async def _get_or_404(blog_id: UUID) -> dict:
    if not (result := await B.select().where(B.id == blog_id).first()):
        raise NotFoundException(detail=f"Blog post with ID {blog_id} not found")
    return result


async def _load_tags(blog_ids: list[UUID]) -> dict[UUID, list[Tag]]:
    """複数ブログのタグを一括読み込み"""
    if not blog_ids:
        return {}
    tag_relations = await BPT.select(BPT.blog_post_id, BPT.tag_id).where(
        BPT.blog_post_id.is_in(blog_ids)
    )
    tag_ids = {r["tag_id"] for r in tag_relations}
    tags_dict = {}
    if tag_ids:
        tags_data = await T.select().where(T.id.is_in(tag_ids))
        tags_dict = {t["id"]: Tag(id=t["id"], name=t["name"]) for t in tags_data}
    result: dict[UUID, list[Tag]] = {bid: [] for bid in blog_ids}
    for rel in tag_relations:
        if tag := tags_dict.get(rel["tag_id"]):
            result[rel["blog_post_id"]].append(tag)
    return result


async def _load_likes(blog_ids: list[UUID], user_id: UUID) -> dict[UUID, dict]:
    """複数ブログのいいね情報を一括読み込み"""
    if not blog_ids:
        return {}
    # いいね数を取得
    like_counts = {}
    for blog_id in blog_ids:
        count = await BLT.count().where(BLT.blog_post_id == blog_id)
        like_counts[blog_id] = count
    # ユーザーがいいね済みか確認
    user_likes = await BLT.select(BLT.blog_post_id).where(
        (BLT.blog_post_id.is_in(blog_ids)) & (BLT.employee_id == user_id)
    )
    liked_ids = {like["blog_post_id"] for like in user_likes}
    return {
        bid: {"count": like_counts.get(bid, 0), "is_liked": bid in liked_ids}
        for bid in blog_ids
    }


@get("/blogs/view")
async def view_blogs(request: Request, page: int = 1) -> Template:
    page_size, total = 10, await B.count()
    blogs = (
        await B.select()
        .order_by(B.created_at, ascending=False)
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    author_ids = {b["author_id"] for b in blogs}
    authors = {}
    if author_ids:
        authors = {
            e["id"]: Employee(id=e["id"], name=e["name"])
            for e in await E.select(E.id, E.name).where(E.id.is_in(author_ids))
        }
    blog_ids = [b["id"] for b in blogs]
    tags_map = await _load_tags(blog_ids)
    likes_map = await _load_likes(blog_ids, request.state.user_id)
    posts = [
        BlogPost(
            id=b["id"],
            author_id=b["author_id"],
            title=b["title"],
            content=b["content"],
            created_at=b["created_at"],
            updated_at=b["updated_at"],
            tags=tags_map.get(b["id"], []),
            like_count=likes_map.get(b["id"], {}).get("count", 0),
            is_liked=likes_map.get(b["id"], {}).get("is_liked", False),
        )
        for b in blogs
    ]
    pagination = ClassicPagination(
        items=posts,
        page_size=page_size,
        current_page=page,
        total_pages=(total + page_size - 1) // page_size,
    )
    return Template(
        "blog_list.html",
        context={
            "pagination": pagination,
            "authors": authors,
            "user_id": request.state.user_id,
            "user_role": request.state.role.value,
        },
    )


@get("/blogs/{blog_id:uuid}/detail")
async def view_blog_detail(request: Request, blog_id: UUID) -> Template:
    result = await _get_or_404(blog_id)
    tags_map = await _load_tags([blog_id])
    likes_map = await _load_likes([blog_id], request.state.user_id)
    post = BlogPost(
        id=result["id"],
        author_id=result["author_id"],
        title=result["title"],
        content=result["content"],
        created_at=result["created_at"],
        updated_at=result["updated_at"],
        tags=tags_map.get(blog_id, []),
        like_count=likes_map.get(blog_id, {}).get("count", 0),
        is_liked=likes_map.get(blog_id, {}).get("is_liked", False),
    )
    author = None
    if (
        author_data := await E.select(E.id, E.name)
        .where(E.id == post.author_id)
        .first()
    ):
        author = Employee(id=author_data["id"], name=author_data["name"])
    return Template(
        "blog_detail.html",
        context={
            "post": post,
            "author": author,
            "user_id": request.state.user_id,
            "user_role": request.state.role.value,
        },
    )


@get("/blogs/tag/{tag_id:uuid}")
async def view_blogs_by_tag(request: Request, tag_id: UUID, page: int = 1) -> Template:
    tag = await T.select().where(T.id == tag_id).first()
    if not tag:
        raise NotFoundException(detail=f"Tag with ID {tag_id} not found")
    tag_obj = Tag(id=tag["id"], name=tag["name"])
    page_size = 10
    # タグに紐づくブログIDを取得
    blog_post_relations = await BPT.select(BPT.blog_post_id).where(BPT.tag_id == tag_id)
    blog_ids = [r["blog_post_id"] for r in blog_post_relations]
    if not blog_ids:
        return Template(
            "blog_tag_list.html",
            context={
                "tag": tag_obj,
                "pagination": ClassicPagination(
                    items=[], page_size=page_size, current_page=page, total_pages=0
                ),
                "authors": {},
                "user_id": request.state.user_id,
                "user_role": request.state.role.value,
            },
        )
    total = len(blog_ids)
    offset = (page - 1) * page_size
    paginated_ids = blog_ids[offset : offset + page_size]
    blogs = (
        await B.select()
        .where(B.id.is_in(paginated_ids))
        .order_by(B.created_at, ascending=False)
    )
    author_ids = {b["author_id"] for b in blogs}
    authors = {}
    if author_ids:
        authors = {
            e["id"]: Employee(id=e["id"], name=e["name"])
            for e in await E.select(E.id, E.name).where(E.id.is_in(author_ids))
        }
    blog_ids_list = [b["id"] for b in blogs]
    tags_map = await _load_tags(blog_ids_list)
    likes_map = await _load_likes(blog_ids_list, request.state.user_id)
    posts = [
        BlogPost(
            id=b["id"],
            author_id=b["author_id"],
            title=b["title"],
            content=b["content"],
            created_at=b["created_at"],
            updated_at=b["updated_at"],
            tags=tags_map.get(b["id"], []),
            like_count=likes_map.get(b["id"], {}).get("count", 0),
            is_liked=likes_map.get(b["id"], {}).get("is_liked", False),
        )
        for b in blogs
    ]
    pagination = ClassicPagination(
        items=posts,
        page_size=page_size,
        current_page=page,
        total_pages=(total + page_size - 1) // page_size,
    )
    return Template(
        "blog_tag_list.html",
        context={
            "tag": tag_obj,
            "pagination": pagination,
            "authors": authors,
            "user_id": request.state.user_id,
            "user_role": request.state.role.value,
        },
    )


@get("/blogs/my")
async def view_my_blogs(request: Request, page: int = 1) -> Template:
    user_id = request.state.user_id
    page_size = 10
    total = await B.count().where(B.author_id == user_id)
    blogs = (
        await B.select()
        .where(B.author_id == user_id)
        .order_by(B.created_at, ascending=False)
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    blog_ids = [b["id"] for b in blogs]
    tags_map = await _load_tags(blog_ids)
    likes_map = await _load_likes(blog_ids, user_id)
    posts = [
        BlogPost(
            id=b["id"],
            author_id=b["author_id"],
            title=b["title"],
            content=b["content"],
            created_at=b["created_at"],
            updated_at=b["updated_at"],
            tags=tags_map.get(b["id"], []),
            like_count=likes_map.get(b["id"], {}).get("count", 0),
            is_liked=likes_map.get(b["id"], {}).get("is_liked", False),
        )
        for b in blogs
    ]
    pagination = ClassicPagination(
        items=posts,
        page_size=page_size,
        current_page=page,
        total_pages=(total + page_size - 1) // page_size,
    )
    return Template(
        "blog_my.html",
        context={
            "pagination": pagination,
            "user_id": user_id,
            "user_role": request.state.role.value,
        },
    )


@get("/blogs/register")
async def show_blog_register_form() -> Template:
    all_tags = [Tag(id=t["id"], name=t["name"]) for t in await T.select()]
    return Template("blog_register.html", context={"success": False, "tags": all_tags})


@post("/blogs/register")
async def register_blog(request: Request, data: FormData) -> Template:
    post = BlogPost(
        author_id=request.state.user_id,
        title=data["title"],
        content=data["content"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    await B(
        id=post.id,
        author_id=post.author_id,
        title=post.title,
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
    ).save()
    # タグ関連を保存
    tag_ids = data.get("tag_ids", "").split(",")
    for tag_id in filter(None, tag_ids):
        await BPT(blog_post_id=post.id, tag_id=UUID(tag_id.strip())).save()
    await delete_cached("blogs:list")
    all_tags = [Tag(id=t["id"], name=t["name"]) for t in await T.select()]
    return Template("blog_register.html", context={"success": True, "tags": all_tags})


@get("/blogs/{blog_id:uuid}/edit")
async def show_blog_edit_form(request: Request, blog_id: UUID) -> Template:
    result = await _get_or_404(blog_id)
    if (
        str(result["author_id"]) != str(request.state.user_id)
        and request.state.role.value != "admin"
    ):
        raise NotFoundException(detail="You don't have permission to edit this post")
    tags_map = await _load_tags([blog_id])
    post = BlogPost(
        id=result["id"],
        author_id=result["author_id"],
        title=result["title"],
        content=result["content"],
        created_at=result["created_at"],
        updated_at=result["updated_at"],
        tags=tags_map.get(blog_id, []),
    )
    all_tags = [Tag(id=t["id"], name=t["name"]) for t in await T.select()]
    return Template("blog_edit.html", context={"post": post, "tags": all_tags})


@post("/blogs/{blog_id:uuid}/edit")
async def edit_blog(request: Request, blog_id: UUID, data: FormData) -> Redirect:
    result = await _get_or_404(blog_id)
    if (
        str(result["author_id"]) != str(request.state.user_id)
        and request.state.role.value != "admin"
    ):
        raise NotFoundException(detail="You don't have permission to edit this post")
    await B.update(
        {
            B.title: data["title"],
            B.content: data["content"],
            B.updated_at: datetime.now(),
        }
    ).where(B.id == blog_id)
    # タグ関連を更新
    await BPT.delete().where(BPT.blog_post_id == blog_id)
    tag_ids = data.get("tag_ids", "").split(",")
    for tag_id in filter(None, tag_ids):
        await BPT(blog_post_id=blog_id, tag_id=UUID(tag_id.strip())).save()
    await delete_cached("blogs:list")
    return Redirect(path="/blogs/view")


@post("/blogs/{blog_id:uuid}/delete")
async def delete_blog(request: Request, blog_id: UUID) -> Redirect:
    result = await _get_or_404(blog_id)
    if (
        str(result["author_id"]) != str(request.state.user_id)
        and request.state.role.value != "admin"
    ):
        raise NotFoundException(detail="You don't have permission to delete this post")
    await B.delete().where(B.id == blog_id)
    await delete_cached("blogs:list")
    return Redirect(path="/blogs/view")


@post("/blogs/{blog_id:uuid}/like")
async def like_blog(request: Request, blog_id: UUID, data: FormData) -> Redirect:
    """いいねを追加"""
    await _get_or_404(blog_id)
    employee_id = request.state.user_id
    # 既にいいね済みか確認
    if not await BLT.exists().where(
        (BLT.blog_post_id == blog_id) & (BLT.employee_id == employee_id)
    ):
        await BLT(
            blog_post_id=blog_id, employee_id=employee_id, created_at=datetime.now()
        ).save()
    # リダイレクト先を取得
    redirect_path = data.get("redirect", "/blogs/view")
    return Redirect(path=redirect_path)


@post("/blogs/{blog_id:uuid}/unlike")
async def unlike_blog(request: Request, blog_id: UUID, data: FormData) -> Redirect:
    """いいねを削除"""
    await _get_or_404(blog_id)
    employee_id = request.state.user_id
    await BLT.delete().where(
        (BLT.blog_post_id == blog_id) & (BLT.employee_id == employee_id)
    )
    # リダイレクト先を取得
    redirect_path = data.get("redirect", "/blogs/view")
    return Redirect(path=redirect_path)


blog_web_router = Router(
    path="",
    route_handlers=[
        view_blogs,
        view_blog_detail,
        view_blogs_by_tag,
        view_my_blogs,
        show_blog_register_form,
        register_blog,
        show_blog_edit_form,
        edit_blog,
        delete_blog,
        like_blog,
        unlike_blog,
    ],
    guards=[session_auth_guard],
)
