from typing import Annotated
from uuid import UUID
from litestar import Request, Router, get, post
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.pagination import ClassicPagination
from litestar.params import Body
from litestar.response import Redirect, Template

from app.auth import admin_guard, session_auth_guard
from app.cache import delete_cached
from models import Department, DepartmentTable as D

FormData = Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)]


async def _get_or_404(department_id: UUID) -> dict:
    """部署を取得、存在しなければ404エラー"""
    if not await D.exists().where(D.id == department_id):
        raise NotFoundException(detail=f"Department with ID {department_id} not found")
    return await D.select().where(D.id == department_id).first()


@get("/departments/view")
async def view_departments(request: Request, page: int = 1) -> Template:
    page_size, total = 10, await D.count()
    departments = [
        Department(id=d["id"], name=d["name"])
        for d in await D.select().limit(page_size).offset((page - 1) * page_size)
    ]
    pagination = ClassicPagination(
        items=departments,
        page_size=page_size,
        current_page=page,
        total_pages=(total + page_size - 1) // page_size,
    )
    return Template(
        template_name="department_list.html",
        context={"pagination": pagination, "user_role": request.state.role.value},
    )


@get("/departments/register", guards=[admin_guard])
async def show_department_register_form() -> Template:
    return Template(
        template_name="department_register.html", context={"success": False}
    )


@post("/departments/register", guards=[admin_guard])
async def register_department(data: FormData) -> Template:
    dept = Department(name=data["name"])
    await D(id=dept.id, name=dept.name).save()
    await delete_cached("departments:list", "dashboard:stats")
    return Template(template_name="department_register.html", context={"success": True})


@get("/departments/{department_id:uuid}/edit", guards=[admin_guard])
async def show_department_edit_form(department_id: UUID) -> Template:
    result = await _get_or_404(department_id)
    return Template(
        template_name="department_edit.html",
        context={"department": Department(id=result["id"], name=result["name"])},
    )


@post("/departments/{department_id:uuid}/edit", guards=[admin_guard])
async def edit_department_form(department_id: UUID, data: FormData) -> Redirect:
    await _get_or_404(department_id)
    await D.update({D.name: data["name"]}).where(D.id == department_id)
    await delete_cached("departments:list", "dashboard:stats")
    return Redirect(path="/departments/view")


@post("/departments/{department_id:uuid}/delete", guards=[admin_guard])
async def delete_department_form(department_id: UUID) -> Redirect:
    await _get_or_404(department_id)
    await D.delete().where(D.id == department_id)
    await delete_cached("departments:list", "dashboard:stats")
    return Redirect(path="/departments/view")


department_web_router = Router(
    path="",
    route_handlers=[
        view_departments,
        show_department_register_form,
        register_department,
        show_department_edit_form,
        edit_department_form,
        delete_department_form,
    ],
    guards=[session_auth_guard],
)
