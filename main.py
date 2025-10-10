from pathlib import Path
from typing import Annotated
from uuid import UUID
from litestar import Litestar, get, post, put, delete
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.params import Body
from litestar.response import Template, Redirect
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from litestar.template.config import TemplateConfig

from models import PC, Employee, Department, PCAssignmentHistory


# In-memory storage
pcs: dict[UUID, PC] = {}
employees: dict[UUID, Employee] = {}
departments: dict[UUID, Department] = {}
pc_assignment_histories: dict[UUID, PCAssignmentHistory] = {}


@post("/pcs", status_code=HTTP_201_CREATED)
async def create_pc(data: PC) -> PC:
    """Create a new PC."""
    pcs[data.id] = data

    # Record initial assignment if assigned_to is set
    if data.assigned_to is not None:
        history = PCAssignmentHistory(pc_id=data.id, employee_id=data.assigned_to)
        pc_assignment_histories[history.id] = history

    return data


@get("/pcs")
async def list_pcs() -> list[PC]:
    """Get all PCs."""
    return list(pcs.values())


@get("/pcs/{pc_id:uuid}")
async def get_pc(pc_id: UUID) -> PC:
    """Get a specific PC by ID."""
    if pc_id not in pcs:
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")
    return pcs[pc_id]


@put("/pcs/{pc_id:uuid}")
async def update_pc(pc_id: UUID, data: PC) -> PC:
    """Update an existing PC."""
    if pc_id not in pcs:
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")

    # Record assignment history if assigned_to changed
    old_pc = pcs[pc_id]
    if old_pc.assigned_to != data.assigned_to:
        history = PCAssignmentHistory(pc_id=pc_id, employee_id=data.assigned_to)
        pc_assignment_histories[history.id] = history

    data.id = pc_id
    pcs[pc_id] = data
    return data


@delete("/pcs/{pc_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_pc(pc_id: UUID) -> None:
    """Delete a PC."""
    if pc_id not in pcs:
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")
    del pcs[pc_id]


@get("/pcs/view")
async def view_pcs() -> Template:
    """View all PCs in HTML."""
    return Template(
        template_name="pc_list.html",
        context={"pcs": list(pcs.values()), "employees": employees},
    )


@get("/pcs/register")
async def show_register_form() -> Template:
    """Show PC registration form."""
    return Template(
        template_name="pc_register.html",
        context={
            "success": False,
            "employees": list(employees.values()),
            "departments": departments,
        },
    )


@post("/pcs/register")
async def register_pc(
    data: Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)],
) -> Template:
    """Register a new PC from form."""
    assigned_to = UUID(data["assigned_to"]) if data.get("assigned_to") else None
    pc = PC(
        name=data["name"],
        model=data["model"],
        serial_number=data["serial_number"],
        assigned_to=assigned_to,
    )
    pcs[pc.id] = pc

    # Record initial assignment if assigned_to is set
    if assigned_to is not None:
        history = PCAssignmentHistory(pc_id=pc.id, employee_id=assigned_to)
        pc_assignment_histories[history.id] = history
    return Template(
        template_name="pc_register.html",
        context={
            "success": True,
            "employees": list(employees.values()),
            "departments": departments,
        },
    )


@get("/pcs/{pc_id:uuid}/edit")
async def show_edit_form(pc_id: UUID) -> Template:
    """Show PC edit form."""
    if pc_id not in pcs:
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")
    return Template(
        template_name="pc_edit.html",
        context={
            "pc": pcs[pc_id],
            "employees": list(employees.values()),
            "departments": departments,
        },
    )


@post("/pcs/{pc_id:uuid}/edit")
async def edit_pc(
    pc_id: UUID,
    data: Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)],
) -> Redirect:
    """Update a PC from form."""
    if pc_id not in pcs:
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")

    # Record assignment history if assigned_to changed
    old_pc = pcs[pc_id]
    assigned_to = UUID(data["assigned_to"]) if data.get("assigned_to") else None
    if old_pc.assigned_to != assigned_to:
        history = PCAssignmentHistory(pc_id=pc_id, employee_id=assigned_to)
        pc_assignment_histories[history.id] = history

    pc = PC(
        id=pc_id,
        name=data["name"],
        model=data["model"],
        serial_number=data["serial_number"],
        assigned_to=assigned_to,
    )
    pcs[pc_id] = pc
    return Redirect(path="/pcs/view")


@post("/pcs/{pc_id:uuid}/delete")
async def delete_pc_form(pc_id: UUID) -> Redirect:
    """Delete a PC from form."""
    if pc_id not in pcs:
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")
    del pcs[pc_id]
    return Redirect(path="/pcs/view")


@get("/pcs/{pc_id:uuid}/history")
async def get_pc_assignment_history(pc_id: UUID) -> list[PCAssignmentHistory]:
    """Get assignment history for a specific PC."""
    if pc_id not in pcs:
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")
    return [h for h in pc_assignment_histories.values() if h.pc_id == pc_id]


@get("/pcs/{pc_id:uuid}/history/view")
async def view_pc_assignment_history(pc_id: UUID) -> Template:
    """View assignment history for a specific PC in HTML."""
    if pc_id not in pcs:
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")
    histories = [h for h in pc_assignment_histories.values() if h.pc_id == pc_id]
    histories.sort(key=lambda h: h.assigned_at, reverse=True)
    return Template(
        template_name="pc_history.html",
        context={
            "pc": pcs[pc_id],
            "histories": histories,
            "employees": employees,
        },
    )


# Employee REST API endpoints
@post("/employees", status_code=HTTP_201_CREATED)
async def create_employee(data: Employee) -> Employee:
    """Create a new employee."""
    employees[data.id] = data
    return data


@get("/employees")
async def list_employees() -> list[Employee]:
    """Get all employees."""
    return list(employees.values())


@get("/employees/{employee_id:uuid}")
async def get_employee(employee_id: UUID) -> Employee:
    """Get a specific employee by ID."""
    if employee_id not in employees:
        raise NotFoundException(detail=f"Employee with ID {employee_id} not found")
    return employees[employee_id]


@put("/employees/{employee_id:uuid}")
async def update_employee(employee_id: UUID, data: Employee) -> Employee:
    """Update an existing employee."""
    if employee_id not in employees:
        raise NotFoundException(detail=f"Employee with ID {employee_id} not found")
    data.id = employee_id
    employees[employee_id] = data
    return data


@delete("/employees/{employee_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_employee(employee_id: UUID) -> None:
    """Delete an employee."""
    if employee_id not in employees:
        raise NotFoundException(detail=f"Employee with ID {employee_id} not found")
    del employees[employee_id]


# Employee HTML form endpoints
@get("/employees/view")
async def view_employees() -> Template:
    """View all employees in HTML."""
    return Template(
        template_name="employee_list.html",
        context={"employees": list(employees.values()), "departments": departments},
    )


@get("/employees/register")
async def show_employee_register_form() -> Template:
    """Show employee registration form."""
    return Template(
        template_name="employee_register.html",
        context={"success": False, "departments": list(departments.values())},
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
    employees[employee.id] = employee
    return Template(
        template_name="employee_register.html",
        context={"success": True, "departments": list(departments.values())},
    )


@get("/employees/{employee_id:uuid}/edit")
async def show_employee_edit_form(employee_id: UUID) -> Template:
    """Show employee edit form."""
    if employee_id not in employees:
        raise NotFoundException(detail=f"Employee with ID {employee_id} not found")
    return Template(
        template_name="employee_edit.html",
        context={
            "employee": employees[employee_id],
            "departments": list(departments.values()),
        },
    )


@post("/employees/{employee_id:uuid}/edit")
async def edit_employee_form(
    employee_id: UUID,
    data: Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)],
) -> Redirect:
    """Update an employee from form."""
    if employee_id not in employees:
        raise NotFoundException(detail=f"Employee with ID {employee_id} not found")

    department_id = UUID(data["department_id"]) if data.get("department_id") else None
    employee = Employee(
        id=employee_id,
        name=data["name"],
        email=data["email"],
        department_id=department_id,
    )
    employees[employee_id] = employee
    return Redirect(path="/employees/view")


@post("/employees/{employee_id:uuid}/delete")
async def delete_employee_form(employee_id: UUID) -> Redirect:
    """Delete an employee from form."""
    if employee_id not in employees:
        raise NotFoundException(detail=f"Employee with ID {employee_id} not found")
    del employees[employee_id]
    return Redirect(path="/employees/view")


# Department REST API endpoints
@post("/departments", status_code=HTTP_201_CREATED)
async def create_department(data: Department) -> Department:
    """Create a new department."""
    departments[data.id] = data
    return data


@get("/departments")
async def list_departments() -> list[Department]:
    """Get all departments."""
    return list(departments.values())


@get("/departments/{department_id:uuid}")
async def get_department(department_id: UUID) -> Department:
    """Get a specific department by ID."""
    if department_id not in departments:
        raise NotFoundException(detail=f"Department with ID {department_id} not found")
    return departments[department_id]


@put("/departments/{department_id:uuid}")
async def update_department(department_id: UUID, data: Department) -> Department:
    """Update an existing department."""
    if department_id not in departments:
        raise NotFoundException(detail=f"Department with ID {department_id} not found")
    data.id = department_id
    departments[department_id] = data
    return data


@delete("/departments/{department_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_department(department_id: UUID) -> None:
    """Delete an department."""
    if department_id not in departments:
        raise NotFoundException(detail=f"Department with ID {department_id} not found")
    del departments[department_id]


# Department HTML form endpoints
@get("/departments/view")
async def view_departments() -> Template:
    """View all departments in HTML."""
    return Template(
        template_name="department_list.html",
        context={"departments": list(departments.values())},
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
    department = Department(
        name=data["name"],
    )
    departments[department.id] = department
    return Template(template_name="department_register.html", context={"success": True})


@get("/departments/{department_id:uuid}/edit")
async def show_department_edit_form(department_id: UUID) -> Template:
    """Show department edit form."""
    if department_id not in departments:
        raise NotFoundException(detail=f"Department with ID {department_id} not found")
    return Template(
        template_name="department_edit.html",
        context={"department": departments[department_id]},
    )


@post("/departments/{department_id:uuid}/edit")
async def edit_department_form(
    department_id: UUID,
    data: Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)],
) -> Redirect:
    """Update an department from form."""
    if department_id not in departments:
        raise NotFoundException(detail=f"Department with ID {department_id} not found")

    department = Department(
        id=department_id,
        name=data["name"],
    )
    departments[department_id] = department
    return Redirect(path="/departments/view")


@post("/departments/{department_id:uuid}/delete")
async def delete_department_form(department_id: UUID) -> Redirect:
    """Delete an employee from form."""
    if department_id not in departments:
        raise NotFoundException(detail=f"Department with ID {department_id} not found")
    del departments[department_id]
    return Redirect(path="/departments/view")


def create_app() -> Litestar:
    return Litestar(
        route_handlers=[
            create_pc,
            list_pcs,
            get_pc,
            update_pc,
            delete_pc,
            view_pcs,
            show_register_form,
            register_pc,
            show_edit_form,
            edit_pc,
            delete_pc_form,
            get_pc_assignment_history,
            view_pc_assignment_history,
            create_employee,
            list_employees,
            get_employee,
            update_employee,
            delete_employee,
            view_employees,
            show_employee_register_form,
            register_employee,
            show_employee_edit_form,
            edit_employee_form,
            delete_employee_form,
            create_department,
            list_departments,
            get_department,
            update_department,
            delete_department,
            view_departments,
            show_department_register_form,
            register_department,
            show_department_edit_form,
            edit_department_form,
            delete_department_form,
        ],
        template_config=TemplateConfig(
            directory=Path("templates"),
            engine=JinjaTemplateEngine,
        ),
    )


app = create_app()
