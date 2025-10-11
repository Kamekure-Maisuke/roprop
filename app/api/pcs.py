from uuid import UUID, uuid4
from litestar import Router, get, post, put, delete
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from sqlalchemy import select

from app.database import get_session
from models import PC, PCModel, PCAssignmentHistory, PCAssignmentHistoryModel


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
