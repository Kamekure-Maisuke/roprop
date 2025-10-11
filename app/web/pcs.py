from typing import Annotated
from uuid import UUID, uuid4
from litestar import Router, get, post
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.params import Body
from litestar.response import Redirect, Template

from models import (
    Department,
    DepartmentTable as D,
    Employee,
    EmployeeTable as E,
    PC,
    PCAssignmentHistory,
    PCAssignmentHistoryTable as H,
    PCTable as P,
)

FormData = Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)]


async def _get_pc_or_404(pc_id: UUID) -> dict:
    if not (result := await P.select().where(P.id == pc_id).first()):
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")
    return result


async def _get_employees_and_departments() -> tuple[
    list[Employee], dict[UUID, Department]
]:
    employees = [
        Employee(
            id=e["id"],
            name=e["name"],
            email=e["email"],
            department_id=e["department_id"],
        )
        for e in await E.select()
    ]
    departments = {
        d["id"]: Department(id=d["id"], name=d["name"]) for d in await D.select()
    }
    return employees, departments


@get("/pcs/view")
async def view_pcs() -> Template:
    pcs = [
        PC(
            id=p["id"],
            name=p["name"],
            model=p["model"],
            serial_number=p["serial_number"],
            assigned_to=p["assigned_to"],
        )
        for p in await P.select()
    ]
    employees = {
        e["id"]: Employee(
            id=e["id"],
            name=e["name"],
            email=e["email"],
            department_id=e["department_id"],
        )
        for e in await E.select()
    }
    return Template(
        template_name="pc_list.html", context={"pcs": pcs, "employees": employees}
    )


@get("/pcs/register")
async def show_register_form() -> Template:
    employees, departments = await _get_employees_and_departments()
    return Template(
        template_name="pc_register.html",
        context={"success": False, "employees": employees, "departments": departments},
    )


@post("/pcs/register")
async def register_pc(data: FormData) -> Template:
    assigned_to = UUID(data["assigned_to"]) if data.get("assigned_to") else None
    pc = PC(
        name=data["name"],
        model=data["model"],
        serial_number=data["serial_number"],
        assigned_to=assigned_to,
    )
    await P(
        id=pc.id,
        name=pc.name,
        model=pc.model,
        serial_number=pc.serial_number,
        assigned_to=pc.assigned_to,
    ).save()
    if assigned_to:
        await H(id=uuid4(), pc_id=pc.id, employee_id=assigned_to).save()
    employees, departments = await _get_employees_and_departments()
    return Template(
        template_name="pc_register.html",
        context={"success": True, "employees": employees, "departments": departments},
    )


@get("/pcs/{pc_id:uuid}/edit")
async def show_edit_form(pc_id: UUID) -> Template:
    result = await _get_pc_or_404(pc_id)
    pc = PC(
        id=result["id"],
        name=result["name"],
        model=result["model"],
        serial_number=result["serial_number"],
        assigned_to=result["assigned_to"],
    )
    employees, departments = await _get_employees_and_departments()
    return Template(
        template_name="pc_edit.html",
        context={"pc": pc, "employees": employees, "departments": departments},
    )


@post("/pcs/{pc_id:uuid}/edit")
async def edit_pc(pc_id: UUID, data: FormData) -> Redirect:
    old = await _get_pc_or_404(pc_id)
    assigned_to = UUID(data["assigned_to"]) if data.get("assigned_to") else None
    if old["assigned_to"] != assigned_to:
        await H(id=uuid4(), pc_id=pc_id, employee_id=assigned_to).save()
    await P.update(
        {
            P.name: data["name"],
            P.model: data["model"],
            P.serial_number: data["serial_number"],
            P.assigned_to: assigned_to,
        }
    ).where(P.id == pc_id)
    return Redirect(path="/pcs/view")


@post("/pcs/{pc_id:uuid}/delete")
async def delete_pc_form(pc_id: UUID) -> Redirect:
    await _get_pc_or_404(pc_id)
    await P.delete().where(P.id == pc_id)
    return Redirect(path="/pcs/view")


@get("/pcs/{pc_id:uuid}/history/view")
async def view_pc_assignment_history(pc_id: UUID) -> Template:
    result = await _get_pc_or_404(pc_id)
    pc = PC(
        id=result["id"],
        name=result["name"],
        model=result["model"],
        serial_number=result["serial_number"],
        assigned_to=result["assigned_to"],
    )
    histories = sorted(
        [
            PCAssignmentHistory(
                id=h["id"],
                pc_id=h["pc_id"],
                employee_id=h["employee_id"],
                assigned_at=h["assigned_at"],
                notes=h["notes"],
            )
            for h in await H.select().where(H.pc_id == pc_id)
        ],
        key=lambda h: h.assigned_at,
        reverse=True,
    )
    employees = {
        e["id"]: Employee(
            id=e["id"],
            name=e["name"],
            email=e["email"],
            department_id=e["department_id"],
        )
        for e in await E.select()
    }
    return Template(
        template_name="pc_history.html",
        context={"pc": pc, "histories": histories, "employees": employees},
    )


@get("/history/view")
async def view_all_assignment_history() -> Template:
    histories = sorted(
        [
            PCAssignmentHistory(
                id=h["id"],
                pc_id=h["pc_id"],
                employee_id=h["employee_id"],
                assigned_at=h["assigned_at"],
                notes=h["notes"],
            )
            for h in await H.select()
        ],
        key=lambda h: h.assigned_at,
        reverse=True,
    )
    pcs = {
        p["id"]: PC(
            id=p["id"],
            name=p["name"],
            model=p["model"],
            serial_number=p["serial_number"],
            assigned_to=p["assigned_to"],
        )
        for p in await P.select()
    }
    employees = {
        e["id"]: Employee(
            id=e["id"],
            name=e["name"],
            email=e["email"],
            department_id=e["department_id"],
        )
        for e in await E.select()
    }
    departments = {
        d["id"]: Department(id=d["id"], name=d["name"]) for d in await D.select()
    }
    return Template(
        template_name="assignment_history.html",
        context={
            "histories": histories,
            "pcs": pcs,
            "employees": employees,
            "departments": departments,
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
