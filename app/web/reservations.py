from typing import Annotated
from uuid import UUID
from datetime import datetime, timedelta
from litestar import Request, Router, get, post
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.pagination import ClassicPagination
from litestar.params import Body
from litestar.response import Redirect, Template

from app.auth import session_auth_guard
from app.cache import delete_cached
from models import (
    MeetingRoomReservationTable as MRR,
    ReservationParticipantTable as RP,
    MeetingRoomTable as MR,
    EmployeeTable as E,
)

FormData = Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)]


async def _get_or_404(reservation_id: UUID) -> dict:
    """予約を取得、存在しなければ404エラー"""
    if not await MRR.exists().where(MRR.id == reservation_id):
        raise NotFoundException(
            detail=f"Reservation with ID {reservation_id} not found"
        )
    return await MRR.select().where(MRR.id == reservation_id).first()


async def _get_participants(reservation_id: UUID) -> list[dict]:
    """予約の参加者情報を取得"""
    participants = await RP.select(RP.employee_id).where(
        RP.reservation_id == reservation_id
    )
    result = []
    for p in participants:
        emp = await E.select().where(E.id == p["employee_id"]).first()
        if emp:
            result.append({"id": emp["id"], "name": emp["name"]})
    return result


@get("/reservations/view")
async def view_reservations(request: Request, page: int = 1) -> Template:
    """予約一覧表示"""
    page_size, total = 10, await MRR.count()

    reservations_data = (
        await MRR.select()
        .order_by(MRR.start_time, ascending=False)
        .limit(page_size)
        .offset((page - 1) * page_size)
    )

    reservations = []
    for r in reservations_data:
        room = await MR.select().where(MR.id == r["meeting_room_id"]).first()
        creator = await E.select().where(E.id == r["created_by"]).first()
        participants = await _get_participants(r["id"])

        reservations.append(
            {
                "id": r["id"],
                "title": r["title"],
                "room_name": room["name"] if room else "不明",
                "start_time": r["start_time"],
                "end_time": r["end_time"],
                "creator_name": creator["name"] if creator else "不明",
                "participants": participants,
            }
        )

    pagination = ClassicPagination(
        items=reservations,
        page_size=page_size,
        current_page=page,
        total_pages=(total + page_size - 1) // page_size,
    )

    return Template(
        template_name="reservation_list.html",
        context={"pagination": pagination, "user_role": request.state.role.value},
    )


@get("/reservations/register")
async def show_reservation_register_form(request: Request) -> Template:
    """予約登録フォーム表示"""
    rooms = [{"id": r["id"], "name": r["name"]} for r in await MR.select()]
    employees = [{"id": e["id"], "name": e["name"]} for e in await E.select()]

    return Template(
        template_name="reservation_register.html",
        context={"success": False, "rooms": rooms, "employees": employees},
    )


@post("/reservations/register")
async def register_reservation(request: Request, data: FormData) -> Template:
    """予約登録処理"""
    reservation_id = UUID(data.get("id")) if data.get("id") else None
    from uuid import uuid4

    if not reservation_id:
        reservation_id = uuid4()

    # 参加者IDリストを取得
    participant_ids = [
        UUID(pid) for pid in data.get("participant_ids", "").split(",") if pid.strip()
    ]

    await MRR(
        id=reservation_id,
        meeting_room_id=UUID(data["meeting_room_id"]),
        title=data["title"],
        start_time=datetime.fromisoformat(data["start_time"]),
        end_time=datetime.fromisoformat(data["end_time"]),
        created_by=request.state.user_id,
        created_at=datetime.now(),
    ).save()

    # 参加者を登録
    for emp_id in participant_ids:
        await RP(
            reservation_id=reservation_id,
            employee_id=emp_id,
        ).save()

    await delete_cached("reservations:list")

    rooms = [{"id": r["id"], "name": r["name"]} for r in await MR.select()]
    employees = [{"id": e["id"], "name": e["name"]} for e in await E.select()]

    return Template(
        template_name="reservation_register.html",
        context={"success": True, "rooms": rooms, "employees": employees},
    )


@get("/reservations/{reservation_id:uuid}/edit")
async def show_reservation_edit_form(reservation_id: UUID) -> Template:
    """予約編集フォーム表示"""
    result = await _get_or_404(reservation_id)
    room = await MR.select().where(MR.id == result["meeting_room_id"]).first()
    participants = await _get_participants(reservation_id)

    rooms = [{"id": r["id"], "name": r["name"]} for r in await MR.select()]
    employees = [{"id": e["id"], "name": e["name"]} for e in await E.select()]

    return Template(
        template_name="reservation_edit.html",
        context={
            "reservation": {
                "id": result["id"],
                "title": result["title"],
                "meeting_room_id": result["meeting_room_id"],
                "room_name": room["name"] if room else "不明",
                "start_time": result["start_time"].strftime("%Y-%m-%dT%H:%M"),
                "end_time": result["end_time"].strftime("%Y-%m-%dT%H:%M"),
            },
            "participants": participants,
            "rooms": rooms,
            "employees": employees,
        },
    )


@post("/reservations/{reservation_id:uuid}/edit")
async def edit_reservation_form(reservation_id: UUID, data: FormData) -> Redirect:
    """予約編集処理"""
    await _get_or_404(reservation_id)

    await MRR.update(
        {
            MRR.title: data["title"],
            MRR.meeting_room_id: UUID(data["meeting_room_id"]),
            MRR.start_time: datetime.fromisoformat(data["start_time"]),
            MRR.end_time: datetime.fromisoformat(data["end_time"]),
        }
    ).where(MRR.id == reservation_id)

    # 参加者を更新
    await RP.delete().where(RP.reservation_id == reservation_id)
    participant_ids = [
        UUID(pid) for pid in data.get("participant_ids", "").split(",") if pid.strip()
    ]
    for emp_id in participant_ids:
        await RP(
            reservation_id=reservation_id,
            employee_id=emp_id,
        ).save()

    await delete_cached("reservations:list")
    return Redirect(path="/reservations/view")


@post("/reservations/{reservation_id:uuid}/delete")
async def delete_reservation_form(reservation_id: UUID) -> Redirect:
    """予約削除処理"""
    await _get_or_404(reservation_id)
    await RP.delete().where(RP.reservation_id == reservation_id)
    await MRR.delete().where(MRR.id == reservation_id)
    await delete_cached("reservations:list")
    return Redirect(path="/reservations/view")


@get("/reservations/room/{room_id:uuid}/availability")
async def get_room_availability_web(room_id: UUID, date: str) -> dict:
    """指定日の会議室の予約状況を取得（Web用）"""
    target_date = datetime.fromisoformat(date).date()
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)

    reservations = await MRR.select().where(
        (MRR.meeting_room_id == room_id)
        & (MRR.start_time >= start_of_day)
        & (MRR.start_time < end_of_day)
    )

    blocked_times = []
    for r in reservations:
        blocked_times.append(
            {
                "start": r["start_time"].isoformat(),
                "end": r["end_time"].isoformat(),
                "title": r["title"],
            }
        )

    return {"date": date, "blocked_times": blocked_times}


reservation_web_router = Router(
    path="",
    route_handlers=[
        view_reservations,
        show_reservation_register_form,
        register_reservation,
        show_reservation_edit_form,
        edit_reservation_form,
        delete_reservation_form,
        get_room_availability_web,
    ],
    guards=[session_auth_guard],
)
