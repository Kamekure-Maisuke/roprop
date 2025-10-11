from typing import Annotated
from uuid import UUID
from litestar import Router, get, post
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.params import Body
from litestar.response import Redirect, Template

from models import Department, DepartmentTable as D

FormData = Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)]


async def _get_or_404(department_id: UUID) -> dict:
    """部署を取得、存在しなければ404エラー"""
    if not (result := await D.select().where(D.id == department_id).first()):
        raise NotFoundException(detail=f"Department with ID {department_id} not found")
    return result


@get("/departments/view")
async def view_departments() -> Template:
    results = await D.select()
    return Template(
        template_name="department_list.html",
        context={
            "departments": [Department(id=d["id"], name=d["name"]) for d in results]
        },
    )


@get("/departments/register")
async def show_department_register_form() -> Template:
    return Template(
        template_name="department_register.html", context={"success": False}
    )


@post("/departments/register")
async def register_department(data: FormData) -> Template:
    dept = Department(name=data["name"])
    await D(id=dept.id, name=dept.name).save()
    return Template(template_name="department_register.html", context={"success": True})


@get("/departments/{department_id:uuid}/edit")
async def show_department_edit_form(department_id: UUID) -> Template:
    result = await _get_or_404(department_id)
    return Template(
        template_name="department_edit.html",
        context={"department": Department(id=result["id"], name=result["name"])},
    )


@post("/departments/{department_id:uuid}/edit")
async def edit_department_form(department_id: UUID, data: FormData) -> Redirect:
    await _get_or_404(department_id)
    await D.update({D.name: data["name"]}).where(D.id == department_id)
    return Redirect(path="/departments/view")


@post("/departments/{department_id:uuid}/delete")
async def delete_department_form(department_id: UUID) -> Redirect:
    await _get_or_404(department_id)
    await D.delete().where(D.id == department_id)
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
)
