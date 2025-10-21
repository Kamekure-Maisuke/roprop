from typing import Annotated
from uuid import UUID
from litestar import Request, Router, get, post
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.pagination import ClassicPagination
from litestar.params import Body
from litestar.response import Redirect, Template

from app.auth import admin_guard, session_auth_guard
from app.cache import delete_cached
from models import MeetingRoom, MeetingRoomTable as MR

FormData = Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)]


async def _get_or_404(room_id: UUID) -> dict:
    """会議室を取得、存在しなければ404エラー"""
    if not await MR.exists().where(MR.id == room_id):
        raise NotFoundException(detail=f"Meeting room with ID {room_id} not found")
    return await MR.select().where(MR.id == room_id).first()


@get("/meeting_rooms/view")
async def view_meeting_rooms(request: Request, page: int = 1) -> Template:
    page_size, total = 10, await MR.count()
    rooms = [
        MeetingRoom(
            id=r["id"],
            name=r["name"],
            capacity=r["capacity"],
            location=r["location"],
            equipment=r["equipment"],
        )
        for r in await MR.select().limit(page_size).offset((page - 1) * page_size)
    ]
    pagination = ClassicPagination(
        items=rooms,
        page_size=page_size,
        current_page=page,
        total_pages=(total + page_size - 1) // page_size,
    )
    return Template(
        template_name="meeting_room_list.html",
        context={"pagination": pagination, "user_role": request.state.role.value},
    )


@get("/meeting_rooms/register", guards=[admin_guard])
async def show_meeting_room_register_form() -> Template:
    return Template(
        template_name="meeting_room_register.html", context={"success": False}
    )


@post("/meeting_rooms/register", guards=[admin_guard])
async def register_meeting_room(data: FormData) -> Template:
    room = MeetingRoom(
        name=data["name"],
        capacity=int(data["capacity"]),
        location=data["location"],
        equipment=data.get("equipment", ""),
    )
    await MR(
        id=room.id,
        name=room.name,
        capacity=room.capacity,
        location=room.location,
        equipment=room.equipment,
    ).save()
    await delete_cached("meeting_rooms:list")
    return Template(
        template_name="meeting_room_register.html", context={"success": True}
    )


@get("/meeting_rooms/{room_id:uuid}/edit", guards=[admin_guard])
async def show_meeting_room_edit_form(room_id: UUID) -> Template:
    result = await _get_or_404(room_id)
    return Template(
        template_name="meeting_room_edit.html",
        context={
            "room": MeetingRoom(
                id=result["id"],
                name=result["name"],
                capacity=result["capacity"],
                location=result["location"],
                equipment=result["equipment"],
            )
        },
    )


@post("/meeting_rooms/{room_id:uuid}/edit", guards=[admin_guard])
async def edit_meeting_room_form(room_id: UUID, data: FormData) -> Redirect:
    await _get_or_404(room_id)
    await MR.update(
        {
            MR.name: data["name"],
            MR.capacity: int(data["capacity"]),
            MR.location: data["location"],
            MR.equipment: data.get("equipment", ""),
        }
    ).where(MR.id == room_id)
    await delete_cached("meeting_rooms:list")
    return Redirect(path="/meeting_rooms/view")


@post("/meeting_rooms/{room_id:uuid}/delete", guards=[admin_guard])
async def delete_meeting_room_form(room_id: UUID) -> Redirect:
    await _get_or_404(room_id)
    await MR.delete().where(MR.id == room_id)
    await delete_cached("meeting_rooms:list")
    return Redirect(path="/meeting_rooms/view")


meeting_room_web_router = Router(
    path="",
    route_handlers=[
        view_meeting_rooms,
        show_meeting_room_register_form,
        register_meeting_room,
        show_meeting_room_edit_form,
        edit_meeting_room_form,
        delete_meeting_room_form,
    ],
    guards=[session_auth_guard],
)
