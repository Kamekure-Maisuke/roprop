from uuid import UUID
from litestar import Router, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.auth import bearer_token_guard
from app.cache import delete_cached
from models import (
    MeetingRoomReservation,
    MeetingRoomReservationTable as MRR,
    ReservationParticipantTable as RP,
)


async def _get_or_404(reservation_id: UUID) -> dict:
    """予約を取得、存在しなければ404エラー"""
    if not await MRR.exists().where(MRR.id == reservation_id):
        raise NotFoundException(
            detail=f"Reservation with ID {reservation_id} not found"
        )
    return await MRR.select().where(MRR.id == reservation_id).first()


async def _get_participants(reservation_id: UUID) -> list[UUID]:
    """予約の参加者ID一覧を取得"""
    participants = await RP.select(RP.employee_id).where(
        RP.reservation_id == reservation_id
    )
    return [p["employee_id"] for p in participants]


def _to_reservation(data: dict, participant_ids: list[UUID] = None) -> dict:
    """辞書から予約オブジェクトに変換"""
    return {
        "id": data["id"],
        "meeting_room_id": data["meeting_room_id"],
        "title": data["title"],
        "start_time": data["start_time"].isoformat(),
        "end_time": data["end_time"].isoformat(),
        "created_by": data["created_by"],
        "created_at": data["created_at"].isoformat(),
        "participant_ids": participant_ids or [],
    }


@post("/reservations", status_code=HTTP_201_CREATED)
async def create_reservation(data: dict) -> dict:
    """予約作成 (participant_idsを含む)"""
    reservation = MeetingRoomReservation(
        meeting_room_id=UUID(data["meeting_room_id"]),
        title=data["title"],
        start_time=data["start_time"],
        end_time=data["end_time"],
        created_by=UUID(data["created_by"]),
        created_at=data.get("created_at"),
    )

    await MRR(
        id=reservation.id,
        meeting_room_id=reservation.meeting_room_id,
        title=reservation.title,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        created_by=reservation.created_by,
        created_at=reservation.created_at,
    ).save()

    # 参加者を登録
    participant_ids = data.get("participant_ids", [])
    for emp_id in participant_ids:
        await RP(
            reservation_id=reservation.id,
            employee_id=UUID(emp_id),
        ).save()

    await delete_cached("reservations:list")
    return _to_reservation(
        {
            "id": reservation.id,
            "meeting_room_id": reservation.meeting_room_id,
            "title": reservation.title,
            "start_time": reservation.start_time,
            "end_time": reservation.end_time,
            "created_by": reservation.created_by,
            "created_at": reservation.created_at,
        },
        participant_ids,
    )


@get("/reservations")
async def list_reservations() -> list[dict]:
    """予約一覧取得"""
    reservations = await MRR.select()
    result = []
    for r in reservations:
        participants = await _get_participants(r["id"])
        result.append(_to_reservation(r, participants))
    return result


@get("/reservations/{reservation_id:uuid}")
async def get_reservation(reservation_id: UUID) -> dict:
    """予約詳細取得"""
    data = await _get_or_404(reservation_id)
    participants = await _get_participants(reservation_id)
    return _to_reservation(data, participants)


@get("/reservations/room/{room_id:uuid}")
async def list_reservations_by_room(room_id: UUID) -> list[dict]:
    """会議室別の予約一覧"""
    reservations = await MRR.select().where(MRR.meeting_room_id == room_id)
    result = []
    for r in reservations:
        participants = await _get_participants(r["id"])
        result.append(_to_reservation(r, participants))
    return result


@put("/reservations/{reservation_id:uuid}")
async def update_reservation(reservation_id: UUID, data: dict) -> dict:
    """予約更新"""
    await _get_or_404(reservation_id)

    await MRR.update(
        {
            MRR.title: data["title"],
            MRR.start_time: data["start_time"],
            MRR.end_time: data["end_time"],
        }
    ).where(MRR.id == reservation_id)

    # 参加者を更新 (既存を削除して再登録)
    await RP.delete().where(RP.reservation_id == reservation_id)
    participant_ids = data.get("participant_ids", [])
    for emp_id in participant_ids:
        await RP(
            reservation_id=reservation_id,
            employee_id=UUID(emp_id),
        ).save()

    await delete_cached("reservations:list")

    updated = await MRR.select().where(MRR.id == reservation_id).first()
    return _to_reservation(updated, participant_ids)


@delete("/reservations/{reservation_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_reservation(reservation_id: UUID) -> None:
    """予約削除"""
    await _get_or_404(reservation_id)
    await RP.delete().where(RP.reservation_id == reservation_id)
    await MRR.delete().where(MRR.id == reservation_id)
    await delete_cached("reservations:list")


reservation_api_router = Router(
    path="",
    route_handlers=[
        create_reservation,
        list_reservations,
        get_reservation,
        list_reservations_by_room,
        update_reservation,
        delete_reservation,
    ],
    guards=[bearer_token_guard],
    security=[{"BearerAuth": []}],
)
