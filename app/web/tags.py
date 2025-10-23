from typing import Annotated
from uuid import UUID

from litestar import Request, Router, get, post
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.pagination import ClassicPagination
from litestar.params import Body
from litestar.response import Redirect, Template

from app.auth import admin_guard, session_auth_guard
from models import Tag
from models import TagTable as T

FormData = Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)]


async def _get_or_404(tag_id: UUID) -> dict:
    """部署を取得、存在しなければ404エラー"""
    if not await T.exists().where(T.id == tag_id):
        raise NotFoundException(detail=f"Tag with ID {tag_id} not found")
    return await T.select().where(T.id == tag_id).first()


@get("/tags/view")
async def view_tags(request: Request, page: int = 1) -> Template:
    page_size, total = 10, await T.count()
    tags = [
        Tag(id=t["id"], name=t["name"])
        for t in await T.select().limit(page_size).offset((page - 1) * page_size)
    ]
    pagination = ClassicPagination(
        items=tags,
        page_size=page_size,
        current_page=page,
        total_pages=(total + page_size - 1) // page_size,
    )
    return Template(
        template_name="tag_list.html",
        context={"pagination": pagination, "user_role": request.state.role.value},
    )


@get("/tags/register", guards=[admin_guard])
async def show_tag_register_form() -> Template:
    return Template(template_name="tag_register.html", context={"success": False})


@post("/tags/register", guards=[admin_guard])
async def register_tag(data: FormData) -> Template:
    tag = Tag(name=data["name"])
    await T(id=tag.id, name=tag.name).save()
    return Template(template_name="tag_register.html", context={"success": True})


@get("/tags/{tag_id:uuid}/edit", guards=[admin_guard])
async def show_tag_edit_form(tag_id: UUID) -> Template:
    result = await _get_or_404(tag_id)
    return Template(
        template_name="tag_edit.html",
        context={"tag": Tag(id=result["id"], name=result["name"])},
    )


@post("/tags/{tag_id:uuid}/edit", guards=[admin_guard])
async def edit_tag_form(tag_id: UUID, data: FormData) -> Redirect:
    await _get_or_404(tag_id)
    await T.update({T.name: data["name"]}).where(T.id == tag_id)
    return Redirect(path="/tags/view")


@post("/tags/{tag_id:uuid}/delete", guards=[admin_guard])
async def delete_tag_form(tag_id: UUID) -> Redirect:
    await _get_or_404(tag_id)
    await T.delete().where(T.id == tag_id)
    return Redirect(path="/tags/view")


tag_web_router = Router(
    path="",
    route_handlers=[
        view_tags,
        show_tag_register_form,
        register_tag,
        show_tag_edit_form,
        edit_tag_form,
        delete_tag_form,
    ],
    guards=[session_auth_guard],
)
