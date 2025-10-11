from uuid import UUID, uuid4
from litestar import Router, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from models import PC, PCAssignmentHistory, PCAssignmentHistoryTable as H, PCTable as P


async def _get_or_404(pc_id: UUID) -> dict:
    if not (result := await P.select().where(P.id == pc_id).first()):
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")
    return result


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
    if data.assigned_to:
        await H(id=uuid4(), pc_id=data.id, employee_id=data.assigned_to).save()
    return data


@get("/pcs")
async def list_pcs() -> list[PC]:
    return [_to_pc(r) for r in await P.select()]


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
    data.id = pc_id
    return data


@delete("/pcs/{pc_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_pc(pc_id: UUID) -> None:
    await _get_or_404(pc_id)
    await P.delete().where(P.id == pc_id)


@get("/pcs/{pc_id:uuid}/history")
async def get_pc_assignment_history(pc_id: UUID) -> list[PCAssignmentHistory]:
    await _get_or_404(pc_id)
    return [_to_history(h) for h in await H.select().where(H.pc_id == pc_id)]


@get("/history")
async def list_all_assignment_history() -> list[PCAssignmentHistory]:
    histories = [_to_history(h) for h in await H.select()]
    return sorted(histories, key=lambda h: h.assigned_at, reverse=True)


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
)
