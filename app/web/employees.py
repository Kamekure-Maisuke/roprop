from typing import Annotated
from uuid import UUID
from litestar import Router, get, post
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.pagination import ClassicPagination
from litestar.params import Body
from litestar.response import Redirect, Template

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
async def register_employee(data: FormData) -> Template:
    dept_id = UUID(data["department_id"]) if data.get("department_id") else None
    emp = Employee(name=data["name"], email=data["email"], department_id=dept_id)
    await E(
        id=emp.id, name=emp.name, email=emp.email, department_id=emp.department_id
    ).save()
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
    return Redirect(path="/employees/view")


@post("/employees/{employee_id:uuid}/delete")
async def delete_employee_form(employee_id: UUID) -> Redirect:
    await _get_or_404(employee_id)
    await E.delete().where(E.id == employee_id)
    return Redirect(path="/employees/view")


employee_web_router = Router(
    path="",
    route_handlers=[
        view_employees,
        show_employee_register_form,
        register_employee,
        show_employee_edit_form,
        edit_employee_form,
        delete_employee_form,
    ],
)
