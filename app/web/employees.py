from typing import Annotated
from uuid import UUID
from litestar import Router, get, post
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.params import Body
from litestar.response import Template, Redirect
from sqlalchemy import select

from app.database import get_session
from models import Employee, EmployeeModel, Department, DepartmentModel


@get("/employees/view")
async def view_employees() -> Template:
    """View all employees in HTML."""
    with get_session() as session:
        employees_result = session.execute(select(EmployeeModel)).scalars().all()
        departments_result = session.execute(select(DepartmentModel)).scalars().all()

        employees_list = [
            Employee(id=e.id, name=e.name, email=e.email, department_id=e.department_id)
            for e in employees_result
        ]
        departments_dict = {
            d.id: Department(id=d.id, name=d.name)
            for d in departments_result
        }

        return Template(
            template_name="employee_list.html",
            context={"employees": employees_list, "departments": departments_dict},
        )


@get("/employees/register")
async def show_employee_register_form() -> Template:
    """Show employee registration form."""
    with get_session() as session:
        departments_result = session.execute(select(DepartmentModel)).scalars().all()
        departments_list = [
            Department(id=d.id, name=d.name)
            for d in departments_result
        ]

        return Template(
            template_name="employee_register.html",
            context={"success": False, "departments": departments_list},
        )


@post("/employees/register")
async def register_employee(
    data: Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)],
) -> Template:
    """Register a new employee from form."""
    department_id = UUID(data["department_id"]) if data.get("department_id") else None
    employee = Employee(
        name=data["name"],
        email=data["email"],
        department_id=department_id,
    )

    with get_session() as session:
        employee_model = EmployeeModel(
            id=employee.id,
            name=employee.name,
            email=employee.email,
            department_id=employee.department_id,
        )
        session.add(employee_model)
        session.commit()

        departments_result = session.execute(select(DepartmentModel)).scalars().all()
        departments_list = [
            Department(id=d.id, name=d.name)
            for d in departments_result
        ]

        return Template(
            template_name="employee_register.html",
            context={"success": True, "departments": departments_list},
        )


@get("/employees/{employee_id:uuid}/edit")
async def show_employee_edit_form(employee_id: UUID) -> Template:
    """Show employee edit form."""
    with get_session() as session:
        employee_model = session.get(EmployeeModel, employee_id)
        if not employee_model:
            raise NotFoundException(detail=f"Employee with ID {employee_id} not found")

        departments_result = session.execute(select(DepartmentModel)).scalars().all()

        employee = Employee(id=employee_model.id, name=employee_model.name,
                          email=employee_model.email, department_id=employee_model.department_id)
        departments_list = [
            Department(id=d.id, name=d.name)
            for d in departments_result
        ]

        return Template(
            template_name="employee_edit.html",
            context={"employee": employee, "departments": departments_list},
        )


@post("/employees/{employee_id:uuid}/edit")
async def edit_employee_form(
    employee_id: UUID,
    data: Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)],
) -> Redirect:
    """Update an employee from form."""
    with get_session() as session:
        employee_model = session.get(EmployeeModel, employee_id)
        if not employee_model:
            raise NotFoundException(detail=f"Employee with ID {employee_id} not found")

        department_id = UUID(data["department_id"]) if data.get("department_id") else None
        employee_model.name = data["name"]
        employee_model.email = data["email"]
        employee_model.department_id = department_id

        session.commit()

    return Redirect(path="/employees/view")


@post("/employees/{employee_id:uuid}/delete")
async def delete_employee_form(employee_id: UUID) -> Redirect:
    """Delete an employee from form."""
    with get_session() as session:
        employee_model = session.get(EmployeeModel, employee_id)
        if not employee_model:
            raise NotFoundException(detail=f"Employee with ID {employee_id} not found")
        session.delete(employee_model)
        session.commit()

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
