from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4
from litestar import Router, get, post
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.pagination import ClassicPagination
from litestar.params import Body
from litestar.response import Redirect, Response, Template
from pydantic import BaseModel

from app.auth import basic_auth_guard
from app.cache import delete_cached
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


class BulkDeleteRequest(BaseModel):
    pc_ids: list[str]


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
async def view_pcs(page: int = 1) -> Template:
    page_size, total = 10, await P.count()
    pcs = [
        PC(
            id=p["id"],
            name=p["name"],
            model=p["model"],
            serial_number=p["serial_number"],
            assigned_to=p["assigned_to"],
        )
        for p in await P.select().limit(page_size).offset((page - 1) * page_size)
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
    pagination = ClassicPagination(
        items=pcs,
        page_size=page_size,
        current_page=page,
        total_pages=(total + page_size - 1) // page_size,
    )
    return Template(
        template_name="pc_list.html",
        context={"pagination": pagination, "employees": employees},
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
    await delete_cached("pcs:list", "history:all", "dashboard:stats")
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
    await delete_cached("pcs:list", "history:all", "dashboard:stats")
    return Redirect(path="/pcs/view")


@post("/pcs/{pc_id:uuid}/delete")
async def delete_pc_form(pc_id: UUID) -> Redirect:
    await _get_pc_or_404(pc_id)
    await P.delete().where(P.id == pc_id)
    await delete_cached("pcs:list", "history:all", "dashboard:stats")
    return Redirect(path="/pcs/view")


@post("/pcs/bulk-delete")
async def bulk_delete_pcs(data: BulkDeleteRequest) -> Response:
    if not data.pc_ids:
        return Response(content="削除するPCが選択されていません", status_code=400)

    pc_ids = [UUID(id) for id in data.pc_ids]
    await P.delete().where(P.id.is_in(pc_ids))
    await delete_cached("pcs:list", "history:all", "dashboard:stats")
    return Response(content=f"{len(pc_ids)}台のPCを削除しました", status_code=200)


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
async def view_all_assignment_history(page: int = 1) -> Template:
    page_size, total = 10, await H.count()
    histories = sorted(
        [
            PCAssignmentHistory(
                id=h["id"],
                pc_id=h["pc_id"],
                employee_id=h["employee_id"],
                assigned_at=h["assigned_at"],
                notes=h["notes"],
            )
            for h in await H.select().limit(page_size).offset((page - 1) * page_size)
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
    pagination = ClassicPagination(
        items=histories,
        page_size=page_size,
        current_page=page,
        total_pages=(total + page_size - 1) // page_size,
    )
    return Template(
        template_name="assignment_history.html",
        context={
            "pagination": pagination,
            "total": total,
            "pcs": pcs,
            "employees": employees,
            "departments": departments,
        },
    )


@get("/pcs/export")
async def export_pcs_tsv() -> Response:
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

    headers = ["ID", "名前", "モデル", "シリアル番号", "割り当て先"]
    rows = ["\t".join(headers)]

    for pc in pcs:
        assigned_name = (
            employees[pc.assigned_to].name
            if pc.assigned_to in employees
            else "未割り当て"
        )
        row = [str(pc.id), pc.name, pc.model, pc.serial_number, assigned_name]
        rows.append("\t".join(row))

    tsv_content = "\n".join(rows)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

    return Response(
        content=tsv_content.encode("utf-8"),
        media_type="text/tab-separated-values; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="pc_list_{timestamp}.tsv"'
        },
    )


@get("/history/export")
async def export_history_tsv() -> Response:
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

    headers = ["割り当て日時", "PC名", "PCモデル", "割り当て先社員", "部署"]
    rows = ["\t".join(headers)]

    for history in histories:
        assigned_at = history.assigned_at.strftime("%Y-%m-%d %H:%M:%S")
        pc_name = pcs[history.pc_id].name if history.pc_id in pcs else "(削除済み)"
        pc_model = pcs[history.pc_id].model if history.pc_id in pcs else "-"

        if history.employee_id and history.employee_id in employees:
            employee_name = employees[history.employee_id].name
            dept_id = employees[history.employee_id].department_id
            department_name = (
                departments[dept_id].name if dept_id and dept_id in departments else "-"
            )
        elif history.employee_id:
            employee_name = "(削除済み)"
            department_name = "-"
        else:
            employee_name = "未割り当て"
            department_name = "-"

        row = [assigned_at, pc_name, pc_model, employee_name, department_name]
        rows.append("\t".join(row))

    tsv_content = "\n".join(rows)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

    return Response(
        content=tsv_content.encode("utf-8"),
        media_type="text/tab-separated-values; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="pc_assignment_history_{timestamp}.tsv"'
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
        bulk_delete_pcs,
        view_pc_assignment_history,
        view_all_assignment_history,
        export_pcs_tsv,
        export_history_tsv,
    ],
    guards=[basic_auth_guard],
)
