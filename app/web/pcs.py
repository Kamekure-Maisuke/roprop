from typing import Annotated
from uuid import UUID, uuid4
from litestar import Router, get, post
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.params import Body
from litestar.response import Template, Redirect
from sqlalchemy import select

from app.database import get_session
from models import PC, PCModel, Employee, EmployeeModel, Department, DepartmentModel, PCAssignmentHistory, PCAssignmentHistoryModel


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


pc_web_router = Router(
    path="",
    route_handlers=[
        view_pcs,
        show_register_form,
        register_pc,
        show_edit_form,
        edit_pc,
        delete_pc_form,
        view_pc_assignment_history,
        view_all_assignment_history,
    ],
)
