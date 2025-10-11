from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4
from litestar import Litestar, get, post, put, delete
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.params import Body
from litestar.response import Template, Redirect
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from litestar.template.config import TemplateConfig
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models import (
    PC, Employee, Department, PCAssignmentHistory,
    PCModel, EmployeeModel, DepartmentModel, PCAssignmentHistoryModel
)

DATABASE_URL = "postgresql://postgres:postgres@localhost:5430/postgres"
engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    return Session(engine)


# PC REST API endpoints
@post("/pcs", status_code=HTTP_201_CREATED)
async def create_pc(data: PC) -> PC:
    """Create a new PC."""
    with get_session() as session:
        pc_model = PCModel(
            id=data.id,
            name=data.name,
            model=data.model,
            serial_number=data.serial_number,
            assigned_to=data.assigned_to,
        )
        session.add(pc_model)

        if data.assigned_to is not None:
            history_model = PCAssignmentHistoryModel(
                id=uuid4(),
                pc_id=data.id,
                employee_id=data.assigned_to,
            )
            session.add(history_model)

        session.commit()

    return data


@get("/pcs")
async def list_pcs() -> list[PC]:
    """Get all PCs."""
    with get_session() as session:
        stmt = select(PCModel)
        results = session.execute(stmt).scalars().all()
        return [
            PC(
                id=r.id,
                name=r.name,
                model=r.model,
                serial_number=r.serial_number,
                assigned_to=r.assigned_to,
            )
            for r in results
        ]


@get("/pcs/{pc_id:uuid}")
async def get_pc(pc_id: UUID) -> PC:
    """Get a specific PC by ID."""
    with get_session() as session:
        pc_model = session.get(PCModel, pc_id)
        if not pc_model:
            raise NotFoundException(detail=f"PC with ID {pc_id} not found")
        return PC(
            id=pc_model.id,
            name=pc_model.name,
            model=pc_model.model,
            serial_number=pc_model.serial_number,
            assigned_to=pc_model.assigned_to,
        )


@put("/pcs/{pc_id:uuid}")
async def update_pc(pc_id: UUID, data: PC) -> PC:
    """Update an existing PC."""
    with get_session() as session:
        pc_model = session.get(PCModel, pc_id)
        if not pc_model:
            raise NotFoundException(detail=f"PC with ID {pc_id} not found")

        old_assigned_to = pc_model.assigned_to
        if old_assigned_to != data.assigned_to:
            history_model = PCAssignmentHistoryModel(
                id=uuid4(),
                pc_id=pc_id,
                employee_id=data.assigned_to,
            )
            session.add(history_model)

        pc_model.name = data.name
        pc_model.model = data.model
        pc_model.serial_number = data.serial_number
        pc_model.assigned_to = data.assigned_to

        session.commit()

    data.id = pc_id
    return data


@delete("/pcs/{pc_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_pc(pc_id: UUID) -> None:
    """Delete a PC."""
    with get_session() as session:
        pc_model = session.get(PCModel, pc_id)
        if not pc_model:
            raise NotFoundException(detail=f"PC with ID {pc_id} not found")
        session.delete(pc_model)
        session.commit()


@get("/pcs/view")
async def view_pcs() -> Template:
    """View all PCs in HTML."""
    with get_session() as session:
        pcs_result = session.execute(select(PCModel)).scalars().all()
        employees_result = session.execute(select(EmployeeModel)).scalars().all()

        pcs_list = [
            PC(id=r.id, name=r.name, model=r.model, serial_number=r.serial_number, assigned_to=r.assigned_to)
            for r in pcs_result
        ]
        employees_dict = {
            e.id: Employee(id=e.id, name=e.name, email=e.email, department_id=e.department_id)
            for e in employees_result
        }

        return Template(
            template_name="pc_list.html",
            context={"pcs": pcs_list, "employees": employees_dict},
        )


@get("/pcs/register")
async def show_register_form() -> Template:
    """Show PC registration form."""
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
            template_name="pc_register.html",
            context={"success": False, "employees": employees_list, "departments": departments_dict},
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

    with get_session() as session:
        pc_model = PCModel(
            id=pc.id,
            name=pc.name,
            model=pc.model,
            serial_number=pc.serial_number,
            assigned_to=pc.assigned_to,
        )
        session.add(pc_model)

        if assigned_to is not None:
            history_model = PCAssignmentHistoryModel(
                id=uuid4(),
                pc_id=pc.id,
                employee_id=assigned_to,
            )
            session.add(history_model)

        session.commit()

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
            template_name="pc_register.html",
            context={"success": True, "employees": employees_list, "departments": departments_dict},
        )


@get("/pcs/{pc_id:uuid}/edit")
async def show_edit_form(pc_id: UUID) -> Template:
    """Show PC edit form."""
    with get_session() as session:
        pc_model = session.get(PCModel, pc_id)
        if not pc_model:
            raise NotFoundException(detail=f"PC with ID {pc_id} not found")

        employees_result = session.execute(select(EmployeeModel)).scalars().all()
        departments_result = session.execute(select(DepartmentModel)).scalars().all()

        pc = PC(id=pc_model.id, name=pc_model.name, model=pc_model.model,
                serial_number=pc_model.serial_number, assigned_to=pc_model.assigned_to)
        employees_list = [
            Employee(id=e.id, name=e.name, email=e.email, department_id=e.department_id)
            for e in employees_result
        ]
        departments_dict = {
            d.id: Department(id=d.id, name=d.name)
            for d in departments_result
        }

        return Template(
            template_name="pc_edit.html",
            context={"pc": pc, "employees": employees_list, "departments": departments_dict},
        )


@post("/pcs/{pc_id:uuid}/edit")
async def edit_pc(
    pc_id: UUID,
    data: Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)],
) -> Redirect:
    """Update a PC from form."""
    with get_session() as session:
        pc_model = session.get(PCModel, pc_id)
        if not pc_model:
            raise NotFoundException(detail=f"PC with ID {pc_id} not found")

        old_assigned_to = pc_model.assigned_to
        assigned_to = UUID(data["assigned_to"]) if data.get("assigned_to") else None

        if old_assigned_to != assigned_to:
            history_model = PCAssignmentHistoryModel(
                id=uuid4(),
                pc_id=pc_id,
                employee_id=assigned_to,
            )
            session.add(history_model)

        pc_model.name = data["name"]
        pc_model.model = data["model"]
        pc_model.serial_number = data["serial_number"]
        pc_model.assigned_to = assigned_to

        session.commit()

    return Redirect(path="/pcs/view")


@post("/pcs/{pc_id:uuid}/delete")
async def delete_pc_form(pc_id: UUID) -> Redirect:
    """Delete a PC from form."""
    with get_session() as session:
        pc_model = session.get(PCModel, pc_id)
        if not pc_model:
            raise NotFoundException(detail=f"PC with ID {pc_id} not found")
        session.delete(pc_model)
        session.commit()

    return Redirect(path="/pcs/view")


@get("/pcs/{pc_id:uuid}/history")
async def get_pc_assignment_history(pc_id: UUID) -> list[PCAssignmentHistory]:
    """Get assignment history for a specific PC."""
    with get_session() as session:
        pc_model = session.get(PCModel, pc_id)
        if not pc_model:
            raise NotFoundException(detail=f"PC with ID {pc_id} not found")

        stmt = select(PCAssignmentHistoryModel).where(PCAssignmentHistoryModel.pc_id == pc_id)
        results = session.execute(stmt).scalars().all()

        return [
            PCAssignmentHistory(
                id=h.id,
                pc_id=h.pc_id,
                employee_id=h.employee_id,
                assigned_at=h.assigned_at,
                notes=h.notes,
            )
            for h in results
        ]


@get("/pcs/{pc_id:uuid}/history/view")
async def view_pc_assignment_history(pc_id: UUID) -> Template:
    """View assignment history for a specific PC in HTML."""
    with get_session() as session:
        pc_model = session.get(PCModel, pc_id)
        if not pc_model:
            raise NotFoundException(detail=f"PC with ID {pc_id} not found")

        stmt = select(PCAssignmentHistoryModel).where(PCAssignmentHistoryModel.pc_id == pc_id)
        histories_result = session.execute(stmt).scalars().all()

        histories = [
            PCAssignmentHistory(id=h.id, pc_id=h.pc_id, employee_id=h.employee_id,
                              assigned_at=h.assigned_at, notes=h.notes)
            for h in histories_result
        ]
        histories.sort(key=lambda h: h.assigned_at, reverse=True)

        employees_result = session.execute(select(EmployeeModel)).scalars().all()
        employees_dict = {
            e.id: Employee(id=e.id, name=e.name, email=e.email, department_id=e.department_id)
            for e in employees_result
        }

        pc = PC(id=pc_model.id, name=pc_model.name, model=pc_model.model,
                serial_number=pc_model.serial_number, assigned_to=pc_model.assigned_to)

        return Template(
            template_name="pc_history.html",
            context={"pc": pc, "histories": histories, "employees": employees_dict},
        )


@get("/history/view")
async def view_all_assignment_history() -> Template:
    """View all PC assignment history in HTML."""
    with get_session() as session:
        histories_result = session.execute(select(PCAssignmentHistoryModel)).scalars().all()
        pcs_result = session.execute(select(PCModel)).scalars().all()
        employees_result = session.execute(select(EmployeeModel)).scalars().all()
        departments_result = session.execute(select(DepartmentModel)).scalars().all()

        histories = [
            PCAssignmentHistory(id=h.id, pc_id=h.pc_id, employee_id=h.employee_id,
                              assigned_at=h.assigned_at, notes=h.notes)
            for h in histories_result
        ]
        histories.sort(key=lambda h: h.assigned_at, reverse=True)

        pcs_dict = {
            p.id: PC(id=p.id, name=p.name, model=p.model, serial_number=p.serial_number, assigned_to=p.assigned_to)
            for p in pcs_result
        }
        employees_dict = {
            e.id: Employee(id=e.id, name=e.name, email=e.email, department_id=e.department_id)
            for e in employees_result
        }
        departments_dict = {
            d.id: Department(id=d.id, name=d.name)
            for d in departments_result
        }

        return Template(
            template_name="assignment_history.html",
            context={
                "histories": histories,
                "pcs": pcs_dict,
                "employees": employees_dict,
                "departments": departments_dict,
            },
        )


@get("/history")
async def list_all_assignment_history() -> list[PCAssignmentHistory]:
    """Get all PC assignment history."""
    with get_session() as session:
        histories_result = session.execute(select(PCAssignmentHistoryModel)).scalars().all()

        histories = [
            PCAssignmentHistory(id=h.id, pc_id=h.pc_id, employee_id=h.employee_id,
                              assigned_at=h.assigned_at, notes=h.notes)
            for h in histories_result
        ]
        return sorted(histories, key=lambda h: h.assigned_at, reverse=True)


# Employee REST API endpoints
@post("/employees", status_code=HTTP_201_CREATED)
async def create_employee(data: Employee) -> Employee:
    """Create a new employee."""
    with get_session() as session:
        employee_model = EmployeeModel(
            id=data.id,
            name=data.name,
            email=data.email,
            department_id=data.department_id,
        )
        session.add(employee_model)
        session.commit()

    return data


@get("/employees")
async def list_employees() -> list[Employee]:
    """Get all employees."""
    with get_session() as session:
        stmt = select(EmployeeModel)
        results = session.execute(stmt).scalars().all()
        return [
            Employee(id=e.id, name=e.name, email=e.email, department_id=e.department_id)
            for e in results
        ]


@get("/employees/{employee_id:uuid}")
async def get_employee(employee_id: UUID) -> Employee:
    """Get a specific employee by ID."""
    with get_session() as session:
        employee_model = session.get(EmployeeModel, employee_id)
        if not employee_model:
            raise NotFoundException(detail=f"Employee with ID {employee_id} not found")
        return Employee(
            id=employee_model.id,
            name=employee_model.name,
            email=employee_model.email,
            department_id=employee_model.department_id,
        )


@put("/employees/{employee_id:uuid}")
async def update_employee(employee_id: UUID, data: Employee) -> Employee:
    """Update an existing employee."""
    with get_session() as session:
        employee_model = session.get(EmployeeModel, employee_id)
        if not employee_model:
            raise NotFoundException(detail=f"Employee with ID {employee_id} not found")

        employee_model.name = data.name
        employee_model.email = data.email
        employee_model.department_id = data.department_id

        session.commit()

    data.id = employee_id
    return data


@delete("/employees/{employee_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_employee(employee_id: UUID) -> None:
    """Delete an employee."""
    with get_session() as session:
        employee_model = session.get(EmployeeModel, employee_id)
        if not employee_model:
            raise NotFoundException(detail=f"Employee with ID {employee_id} not found")
        session.delete(employee_model)
        session.commit()


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


# Department REST API endpoints
@post("/departments", status_code=HTTP_201_CREATED)
async def create_department(data: Department) -> Department:
    """Create a new department."""
    with get_session() as session:
        department_model = DepartmentModel(
            id=data.id,
            name=data.name,
        )
        session.add(department_model)
        session.commit()

    return data


@get("/departments")
async def list_departments() -> list[Department]:
    """Get all departments."""
    with get_session() as session:
        stmt = select(DepartmentModel)
        results = session.execute(stmt).scalars().all()
        return [
            Department(id=d.id, name=d.name)
            for d in results
        ]


@get("/departments/{department_id:uuid}")
async def get_department(department_id: UUID) -> Department:
    """Get a specific department by ID."""
    with get_session() as session:
        department_model = session.get(DepartmentModel, department_id)
        if not department_model:
            raise NotFoundException(detail=f"Department with ID {department_id} not found")
        return Department(id=department_model.id, name=department_model.name)


@put("/departments/{department_id:uuid}")
async def update_department(department_id: UUID, data: Department) -> Department:
    """Update an existing department."""
    with get_session() as session:
        department_model = session.get(DepartmentModel, department_id)
        if not department_model:
            raise NotFoundException(detail=f"Department with ID {department_id} not found")

        department_model.name = data.name
        session.commit()

    data.id = department_id
    return data


@delete("/departments/{department_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_department(department_id: UUID) -> None:
    """Delete an department."""
    with get_session() as session:
        department_model = session.get(DepartmentModel, department_id)
        if not department_model:
            raise NotFoundException(detail=f"Department with ID {department_id} not found")
        session.delete(department_model)
        session.commit()


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


@get("/dashboard")
async def view_dashboard() -> Template:
    """View resource statistics dashboard."""
    with get_session() as session:
        departments_result = session.execute(select(DepartmentModel)).scalars().all()
        employees_result = session.execute(select(EmployeeModel)).scalars().all()
        pcs_result = session.execute(select(PCModel)).scalars().all()

        dept_stats: dict[UUID, dict[str, str | int]] = {}
        unassigned_pc_count = 0

        for dept in departments_result:
            dept_stats[dept.id] = {
                "name": dept.name,
                "employee_count": 0,
                "pc_count": 0,
            }

        for emp in employees_result:
            if emp.department_id and emp.department_id in dept_stats:
                count = dept_stats[emp.department_id]["employee_count"]
                assert isinstance(count, int)
                dept_stats[emp.department_id]["employee_count"] = count + 1

        employees_dict = {e.id: e for e in employees_result}
        for pc in pcs_result:
            if pc.assigned_to:
                emp = employees_dict.get(pc.assigned_to)
                if emp and emp.department_id and emp.department_id in dept_stats:
                    count = dept_stats[emp.department_id]["pc_count"]
                    assert isinstance(count, int)
                    dept_stats[emp.department_id]["pc_count"] = count + 1
            else:
                unassigned_pc_count += 1

        return Template(
            template_name="dashboard.html",
            context={
                "dept_stats": list(dept_stats.values()),
                "unassigned_pc_count": unassigned_pc_count,
                "total_pcs": len(pcs_result),
                "total_employees": len(employees_result),
                "total_departments": len(departments_result),
            },
        )


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
            view_all_assignment_history,
            list_all_assignment_history,
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
            view_dashboard,
        ],
        template_config=TemplateConfig(
            directory=Path("templates"),
            engine=JinjaTemplateEngine,
        ),
    )


app = create_app()
