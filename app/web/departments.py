from typing import Annotated
from uuid import UUID
from litestar import Router, get, post
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.params import Body
from litestar.response import Template, Redirect
from sqlalchemy import select

from app.database import get_session
from models import Department, DepartmentModel


@get("/departments/view")
async def view_departments() -> Template:
    """View all departments in HTML."""
    with get_session() as session:
        departments_result = session.execute(select(DepartmentModel)).scalars().all()
        departments_list = [
            Department(id=d.id, name=d.name)
            for d in departments_result
        ]

        return Template(
            template_name="department_list.html",
            context={"departments": departments_list},
        )


@get("/departments/register")
async def show_department_register_form() -> Template:
    """Show department registration form."""
    return Template(
        template_name="department_register.html", context={"success": False}
    )


@post("/departments/register")
async def register_department(
    data: Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)],
) -> Template:
    """Register a new employee from form."""
    department = Department(name=data["name"])

    with get_session() as session:
        department_model = DepartmentModel(
            id=department.id,
            name=department.name,
        )
        session.add(department_model)
        session.commit()

    return Template(template_name="department_register.html", context={"success": True})


@get("/departments/{department_id:uuid}/edit")
async def show_department_edit_form(department_id: UUID) -> Template:
    """Show department edit form."""
    with get_session() as session:
        department_model = session.get(DepartmentModel, department_id)
        if not department_model:
            raise NotFoundException(detail=f"Department with ID {department_id} not found")

        department = Department(id=department_model.id, name=department_model.name)

        return Template(
            template_name="department_edit.html",
            context={"department": department},
        )


@post("/departments/{department_id:uuid}/edit")
async def edit_department_form(
    department_id: UUID,
    data: Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)],
) -> Redirect:
    """Update an department from form."""
    with get_session() as session:
        department_model = session.get(DepartmentModel, department_id)
        if not department_model:
            raise NotFoundException(detail=f"Department with ID {department_id} not found")

        department_model.name = data["name"]
        session.commit()

    return Redirect(path="/departments/view")


@post("/departments/{department_id:uuid}/delete")
async def delete_department_form(department_id: UUID) -> Redirect:
    """Delete an employee from form."""
    with get_session() as session:
        department_model = session.get(DepartmentModel, department_id)
        if not department_model:
            raise NotFoundException(detail=f"Department with ID {department_id} not found")
        session.delete(department_model)
        session.commit()

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
