from typing import Annotated
from uuid import UUID

from litestar import Request, Router, get, post
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.pagination import ClassicPagination
from litestar.params import Body
from litestar.response import Redirect, Response, Template

from app.auth import session_auth_guard
from app.cache import delete_cached
from app.utils import process_profile_image
from models import Department, DepartmentTable as D, Employee, EmployeeTable as E

FormData = Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)]


async def _get_or_404(employee_id: UUID) -> dict:
    if not (result := await E.select().where(E.id == employee_id).first()):
        raise NotFoundException(detail=f"Employee with ID {employee_id} not found")
    return result


async def _get_departments() -> list[Department]:
    return [Department(id=d["id"], name=d["name"]) for d in await D.select()]


@get("/employees/view")
async def view_employees(page: int = 1) -> Template:
    page_size, total = 10, await E.count()
    employees = [
        Employee(
            id=e["id"],
            name=e["name"],
            email=e["email"],
            department_id=e["department_id"],
        )
        for e in await E.select().limit(page_size).offset((page - 1) * page_size)
    ]
    departments = {
        d["id"]: Department(id=d["id"], name=d["name"]) for d in await D.select()
    }
    pagination = ClassicPagination(
        items=employees,
        page_size=page_size,
        current_page=page,
        total_pages=(total + page_size - 1) // page_size,
    )
    return Template(
        template_name="employee_list.html",
        context={"pagination": pagination, "departments": departments},
    )


@get("/employees/register")
async def show_employee_register_form() -> Template:
    return Template(
        template_name="employee_register.html",
        context={"success": False, "departments": await _get_departments()},
    )


@post("/employees/register")
async def register_employee(request: Request) -> Template:
    form = await request.form()
    dept_id = UUID(form["department_id"]) if form.get("department_id") else None
    emp = Employee(name=form["name"], email=form["email"], department_id=dept_id)

    profile_image = None
    if file := form.get("profile_image"):
        try:
            profile_image = process_profile_image(await file.read())
        except ValueError:
            pass

    await E(
        id=emp.id,
        name=emp.name,
        email=emp.email,
        department_id=emp.department_id,
        profile_image=profile_image,
    ).save()
    await delete_cached("employees:list", "dashboard:stats")
    return Template(
        template_name="employee_register.html",
        context={"success": True, "departments": await _get_departments()},
    )


@get("/employees/{employee_id:uuid}/edit")
async def show_employee_edit_form(employee_id: UUID) -> Template:
    result = await _get_or_404(employee_id)
    emp = Employee(
        id=result["id"],
        name=result["name"],
        email=result["email"],
        department_id=result["department_id"],
    )
    return Template(
        template_name="employee_edit.html",
        context={"employee": emp, "departments": await _get_departments()},
    )


@post("/employees/{employee_id:uuid}/edit")
async def edit_employee_form(employee_id: UUID, data: FormData) -> Redirect:
    await _get_or_404(employee_id)
    dept_id = UUID(data["department_id"]) if data.get("department_id") else None
    await E.update(
        {E.name: data["name"], E.email: data["email"], E.department_id: dept_id}
    ).where(E.id == employee_id)
    await delete_cached("employees:list", "dashboard:stats")
    return Redirect(path="/employees/view")


@post("/employees/{employee_id:uuid}/delete")
async def delete_employee_form(employee_id: UUID) -> Redirect:
    await _get_or_404(employee_id)
    await E.delete().where(E.id == employee_id)
    await delete_cached("employees:list", "dashboard:stats")
    return Redirect(path="/employees/view")


@post("/employees/{employee_id:uuid}/upload-image")
async def upload_employee_image(employee_id: UUID, request: Request) -> Redirect:
    await _get_or_404(employee_id)
    form = await request.form()
    if file := form.get("data"):
        try:
            processed = process_profile_image(await file.read())
            await E.update({E.profile_image: processed}).where(E.id == employee_id)
        except ValueError:
            pass
    return Redirect(path=f"/employees/{employee_id}/edit")


@get("/employees/{employee_id:uuid}/image")
async def get_employee_image(employee_id: UUID) -> Response:
    emp = await _get_or_404(employee_id)
    if not (img := emp.get("profile_image")):
        # 1x1透明GIF
        return Response(
            content=b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01\x44\x00\x3b",
            media_type="image/gif",
        )
    return Response(content=bytes(img), media_type="image/webp")


employee_web_router = Router(
    path="",
    route_handlers=[
        view_employees,
        show_employee_register_form,
        register_employee,
        show_employee_edit_form,
        edit_employee_form,
        delete_employee_form,
        upload_employee_image,
        get_employee_image,
    ],
    guards=[session_auth_guard],
)
