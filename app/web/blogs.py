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
from models import BlogPost, BlogPostTable as B, Employee, EmployeeTable as E

FormData = Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)]


async def _get_or_404(blog_id: UUID) -> dict:
    if not (result := await B.select().where(B.id == blog_id).first()):
        raise NotFoundException(detail=f"Blog post with ID {blog_id} not found")
    return result


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
    posts = [
        BlogPost(
            id=b["id"],
            author_id=b["author_id"],
            title=b["title"],
            content=b["content"],
            created_at=b["created_at"],
            updated_at=b["updated_at"],
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
    post = BlogPost(
        id=result["id"],
        author_id=result["author_id"],
        title=result["title"],
        content=result["content"],
        created_at=result["created_at"],
        updated_at=result["updated_at"],
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
    posts = [
        BlogPost(
            id=b["id"],
            author_id=b["author_id"],
            title=b["title"],
            content=b["content"],
            created_at=b["created_at"],
            updated_at=b["updated_at"],
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
    return Template("blog_register.html", context={"success": False})


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
    await delete_cached("blogs:list")
    return Template("blog_register.html", context={"success": True})


@get("/blogs/{blog_id:uuid}/edit")
async def show_blog_edit_form(request: Request, blog_id: UUID) -> Template:
    result = await _get_or_404(blog_id)
    if (
        str(result["author_id"]) != str(request.state.user_id)
        and request.state.role.value != "admin"
    ):
        raise NotFoundException(detail="You don't have permission to edit this post")
    post = BlogPost(
        id=result["id"],
        author_id=result["author_id"],
        title=result["title"],
        content=result["content"],
        created_at=result["created_at"],
        updated_at=result["updated_at"],
    )
    return Template("blog_edit.html", context={"post": post})


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


blog_web_router = Router(
    path="",
    route_handlers=[
        view_blogs,
        view_blog_detail,
        view_my_blogs,
        show_blog_register_form,
        register_blog,
        show_blog_edit_form,
        edit_blog,
        delete_blog,
    ],
    guards=[session_auth_guard],
)
