from uuid import UUID

from litestar import Router, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.auth import bearer_token_guard
from app.cache import delete_cached, get_cached, set_cached
from models import MeetingRoom
from models import MeetingRoomTable as MR


async def _get_or_404(room_id: UUID) -> dict:
    """会議室を取得、存在しなければ404エラー"""
    if not await MR.exists().where(MR.id == room_id):
        raise NotFoundException(detail=f"Meeting room with ID {room_id} not found")
    return await MR.select().where(MR.id == room_id).first()


def _to_meeting_room(data: dict) -> MeetingRoom:
    """辞書からMeetingRoomオブジェクトに変換"""
    return MeetingRoom(
        id=data["id"],
        name=data["name"],
        capacity=data["capacity"],
        location=data["location"],
        equipment=data["equipment"],
    )


@post("/meeting_rooms", status_code=HTTP_201_CREATED)
async def create_meeting_room(data: MeetingRoom) -> MeetingRoom:
    await MR(
        id=data.id,
        name=data.name,
        capacity=data.capacity,
        location=data.location,
        equipment=data.equipment,
    ).save()
    await delete_cached("meeting_rooms:list")
    return data


@get("/meeting_rooms")
async def list_meeting_rooms() -> list[MeetingRoom]:
    if cached := await get_cached("meeting_rooms:list"):
        return [MeetingRoom(**d) for d in cached]
    result = [_to_meeting_room(d) for d in await MR.select()]
    await set_cached("meeting_rooms:list", [d.__dict__ for d in result])
    return result


@get("/meeting_rooms/{room_id:uuid}")
async def get_meeting_room(room_id: UUID) -> MeetingRoom:
    return _to_meeting_room(await _get_or_404(room_id))


@put("/meeting_rooms/{room_id:uuid}")
async def update_meeting_room(room_id: UUID, data: MeetingRoom) -> MeetingRoom:
    await _get_or_404(room_id)
    await MR.update(
        {
            MR.name: data.name,
            MR.capacity: data.capacity,
            MR.location: data.location,
            MR.equipment: data.equipment,
        }
    ).where(MR.id == room_id)
    await delete_cached("meeting_rooms:list")
    data.id = room_id
    return data


@delete("/meeting_rooms/{room_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_meeting_room(room_id: UUID) -> None:
    await _get_or_404(room_id)
    await MR.delete().where(MR.id == room_id)
    await delete_cached("meeting_rooms:list")


meeting_room_api_router = Router(
    path="",
    route_handlers=[
        create_meeting_room,
        list_meeting_rooms,
        get_meeting_room,
        update_meeting_room,
        delete_meeting_room,
    ],
    guards=[bearer_token_guard],
    security=[{"BearerAuth": []}],
)
