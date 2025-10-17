from typing import Annotated
from uuid import UUID

from litestar import Request, Router, get, post
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.pagination import ClassicPagination
from litestar.params import Body
from litestar.response import Redirect, Response, Template

from app.auth import admin_guard, session_auth_guard
from app.cache import delete_cached
from app.utils import process_profile_image
from models import Department, DepartmentTable as D, Employee, EmployeeTable as E, Role

FormData = Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)]


async def _get_or_404(employee_id: UUID) -> dict:
    if not (result := await E.select().where(E.id == employee_id).first()):
        raise NotFoundException(detail=f"Employee with ID {employee_id} not found")
    return result


async def _get_departments() -> list[Department]:
    return [Department(id=d["id"], name=d["name"]) for d in await D.select()]


@get("/employees/{employee_id:uuid}/show")
async def show_employee_detail(employee_id: UUID) -> Template:
    result = await _get_or_404(employee_id)
    emp = Employee(
        id=result["id"],
        name=result["name"],
        email=result["email"],
        department_id=result["department_id"],
        resignation_date=result.get("resignation_date"),
        transfer_date=result.get("transfer_date"),
        role=Role(result.get("role", Role.USER.value)),
    )
    department = None
    if emp.department_id and (
        dept := await D.select().where(D.id == emp.department_id).first()
    ):
        department = Department(id=dept["id"], name=dept["name"])
    return Template(
        "employee_detail.html", context={"employee": emp, "department": department}
    )


@get("/employees/view")
async def view_employees(request: Request, page: int = 1) -> Template:
    page_size, total = 10, await E.count()
    employees = [
        Employee(
            id=e["id"],
            name=e["name"],
            email=e["email"],
            department_id=e["department_id"],
            resignation_date=e.get("resignation_date"),
            transfer_date=e.get("transfer_date"),
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
        context={
            "pagination": pagination,
            "departments": departments,
            "user_role": request.state.role.value,
        },
    )


@get("/employees/register", guards=[admin_guard])
async def show_employee_register_form() -> Template:
    return Template(
        template_name="employee_register.html",
        context={"success": False, "departments": await _get_departments()},
    )


@post("/employees/register", guards=[admin_guard])
async def register_employee(request: Request) -> Template:
    from datetime import datetime

    form = await request.form()
    dept_id = UUID(form["department_id"]) if form.get("department_id") else None
    resignation_date = (
        datetime.fromisoformat(form["resignation_date"]).date()
        if form.get("resignation_date")
        else None
    )
    transfer_date = (
        datetime.fromisoformat(form["transfer_date"]).date()
        if form.get("transfer_date")
        else None
    )
    role = Role(form.get("role", Role.USER.value))
    emp = Employee(
        name=form["name"],
        email=form["email"],
        department_id=dept_id,
        resignation_date=resignation_date,
        transfer_date=transfer_date,
        role=role,
    )

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
        resignation_date=emp.resignation_date,
        transfer_date=emp.transfer_date,
        role=emp.role.value,
    ).save()
    await delete_cached("employees:list", "dashboard:stats")
    return Template(
        template_name="employee_register.html",
        context={"success": True, "departments": await _get_departments()},
    )


@get("/employees/{employee_id:uuid}/edit", guards=[admin_guard])
async def show_employee_edit_form(employee_id: UUID) -> Template:
    result = await _get_or_404(employee_id)
    emp = Employee(
        id=result["id"],
        name=result["name"],
        email=result["email"],
        department_id=result["department_id"],
        resignation_date=result.get("resignation_date"),
        transfer_date=result.get("transfer_date"),
        role=Role(result.get("role", Role.USER.value)),
    )
    return Template(
        template_name="employee_edit.html",
        context={"employee": emp, "departments": await _get_departments()},
    )


@post("/employees/{employee_id:uuid}/edit", guards=[admin_guard])
async def edit_employee_form(employee_id: UUID, data: FormData) -> Redirect:
    from datetime import datetime

    await _get_or_404(employee_id)
    dept_id = UUID(data["department_id"]) if data.get("department_id") else None
    resignation_date = (
        datetime.fromisoformat(data["resignation_date"]).date()
        if data.get("resignation_date")
        else None
    )
    transfer_date = (
        datetime.fromisoformat(data["transfer_date"]).date()
        if data.get("transfer_date")
        else None
    )
    role = Role(data.get("role", Role.USER.value))
    await E.update(
        {
            E.name: data["name"],
            E.email: data["email"],
            E.department_id: dept_id,
            E.resignation_date: resignation_date,
            E.transfer_date: transfer_date,
            E.role: role.value,
        }
    ).where(E.id == employee_id)
    await delete_cached("employees:list", "dashboard:stats")
    return Redirect(path="/employees/view")


@post("/employees/{employee_id:uuid}/delete", guards=[admin_guard])
async def delete_employee_form(employee_id: UUID) -> Redirect:
    await _get_or_404(employee_id)
    await E.delete().where(E.id == employee_id)
    await delete_cached("employees:list", "dashboard:stats")
    return Redirect(path="/employees/view")


@post("/employees/{employee_id:uuid}/upload-image", guards=[admin_guard])
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


@get("/mypage")
async def view_mypage(request: Request) -> Template:
    from models import PCTable as P

    user_id = request.state.user_id
    emp = await _get_or_404(user_id)
    employee = Employee(
        id=emp["id"],
        name=emp["name"],
        email=emp["email"],
        department_id=emp["department_id"],
        profile_image=emp.get("profile_image"),
        role=Role(emp.get("role", Role.USER.value)),
    )
    department = None
    if emp["department_id"]:
        if dept := await D.select().where(D.id == emp["department_id"]).first():
            department = Department(id=dept["id"], name=dept["name"])
    assigned_pc = None
    if pc := await P.select().where(P.assigned_to == user_id).first():
        from models import PC

        assigned_pc = PC(
            id=pc["id"],
            name=pc["name"],
            model=pc["model"],
            serial_number=pc["serial_number"],
        )
    return Template(
        "mypage.html",
        context={
            "employee": employee,
            "department": department,
            "assigned_pc": assigned_pc,
        },
    )


employee_web_router = Router(
    path="",
    route_handlers=[
        show_employee_detail,
        view_employees,
        show_employee_register_form,
        register_employee,
        show_employee_edit_form,
        edit_employee_form,
        delete_employee_form,
        upload_employee_image,
        get_employee_image,
        view_mypage,
    ],
    guards=[session_auth_guard],
)
