from uuid import UUID, uuid4

from litestar import Router, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.auth import bearer_token_guard
from app.cache import delete_cached, get_cached, set_cached
from app.slack import (
    format_pc_created,
    format_pc_deleted,
    format_pc_updated,
    notify_slack,
)
from models import (
    PC,
    PCAssignmentHistory,
)
from models import (
    PCAssignmentHistoryTable as H,
)
from models import (
    PCTable as P,
)


async def _get_or_404(pc_id: UUID) -> dict:
    if not await P.exists().where(P.id == pc_id):
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")
    return await P.select().where(P.id == pc_id).first()


def _to_pc(data: dict) -> PC:
    return PC(
        id=data["id"],
        name=data["name"],
        model=data["model"],
        serial_number=data["serial_number"],
        assigned_to=data["assigned_to"],
    )


def _to_history(data: dict) -> PCAssignmentHistory:
    return PCAssignmentHistory(
        id=data["id"],
        pc_id=data["pc_id"],
        employee_id=data["employee_id"],
        assigned_at=data["assigned_at"],
        notes=data["notes"],
    )


@post("/pcs", status_code=HTTP_201_CREATED)
async def create_pc(data: PC) -> PC:
    await P(
        id=data.id,
        name=data.name,
        model=data.model,
        serial_number=data.serial_number,
        assigned_to=data.assigned_to,
    ).save()

    # 履歴作成
    if data.assigned_to:
        await H(id=uuid4(), pc_id=data.id, employee_id=data.assigned_to).save()

    # キャッシュ削除
    await delete_cached("pcs:list", "history:all", "dashboard:stats")

    # Slack通知
    assigned_name = None
    if data.assigned_to:
        pc_with_employee = (
            await P.select(P.assigned_to.name).where(P.id == data.id).first()
        )
        if pc_with_employee and pc_with_employee.get("assigned_to.name"):
            assigned_name = pc_with_employee["assigned_to.name"]
    await notify_slack(
        format_pc_created(
            data.name, data.id, data.model, data.serial_number, assigned_name
        )
    )

    return data


@get("/pcs")
async def list_pcs() -> list[PC]:
    if cached := await get_cached("pcs:list"):
        return [PC(**p) for p in cached]
    result = [_to_pc(r) for r in await P.select(P.all_columns())]
    await set_cached("pcs:list", [p.__dict__ for p in result])
    return result


@get("/pcs/{pc_id:uuid}")
async def get_pc(pc_id: UUID) -> PC:
    return _to_pc(await _get_or_404(pc_id))


@put("/pcs/{pc_id:uuid}")
async def update_pc(pc_id: UUID, data: PC) -> PC:
    old = await _get_or_404(pc_id)
    if old["assigned_to"] != data.assigned_to:
        await H(id=uuid4(), pc_id=pc_id, employee_id=data.assigned_to).save()
    await P.update(
        {
            P.name: data.name,
            P.model: data.model,
            P.serial_number: data.serial_number,
            P.assigned_to: data.assigned_to,
        }
    ).where(P.id == pc_id)

    # キャッシュ削除
    await delete_cached("pcs:list", "history:all", "dashboard:stats")

    # Slack通知
    assigned_name = None
    if data.assigned_to:
        pc_with_employee = (
            await P.select(P.assigned_to.name).where(P.id == pc_id).first()
        )
        if pc_with_employee and pc_with_employee.get("assigned_to.name"):
            assigned_name = pc_with_employee["assigned_to.name"]
    await notify_slack(
        format_pc_updated(
            data.name, pc_id, data.model, data.serial_number, assigned_name
        )
    )

    data.id = pc_id
    return data


@delete("/pcs/{pc_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_pc(pc_id: UUID) -> None:
    pc = await _get_or_404(pc_id)
    await P.delete().where(P.id == pc_id)

    # キャッシュ削除
    await delete_cached("pcs:list", "history:all", "dashboard:stats")

    # Slack通知
    await notify_slack(
        format_pc_deleted(pc["name"], pc_id, pc["model"], pc["serial_number"])
    )


@get("/pcs/{pc_id:uuid}/history")
async def get_pc_assignment_history(pc_id: UUID) -> list[PCAssignmentHistory]:
    await _get_or_404(pc_id)
    return [_to_history(h) for h in await H.select().where(H.pc_id == pc_id)]


@get("/history")
async def list_all_assignment_history() -> list[PCAssignmentHistory]:
    if cached := await get_cached("history:all"):
        return [PCAssignmentHistory(**h) for h in cached]
    result = [
        _to_history(h)
        for h in await H.select().order_by(H.assigned_at, ascending=False)
    ]
    await set_cached("history:all", [h.__dict__ for h in result])
    return result


pc_api_router = Router(
    path="",
    route_handlers=[
        create_pc,
        list_pcs,
        get_pc,
        update_pc,
        delete_pc,
        get_pc_assignment_history,
        list_all_assignment_history,
    ],
    guards=[bearer_token_guard],
    security=[{"BearerAuth": []}],
)
