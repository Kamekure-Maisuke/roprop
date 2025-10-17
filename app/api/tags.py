from uuid import UUID
from litestar import Router, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.auth import bearer_token_guard
from models import Tag, TagTable as T


async def _get_or_404(tag_id: UUID) -> dict:
    """部署を取得、存在しなければ404エラー"""
    if not (result := await T.select().where(T.id == tag_id).first()):
        raise NotFoundException(detail=f"Tag with ID {tag_id} not found")
    return result


def _to_tag(data: dict) -> Tag:
    """辞書からTagオブジェクトに変換"""
    return Tag(id=data["id"], name=data["name"])


@post("/tags", status_code=HTTP_201_CREATED)
async def create_tag(data: Tag) -> Tag:
    await T(id=data.id, name=data.name).save()
    return data


@get("/tags")
async def list_tags() -> list[Tag]:
    result = [_to_tag(t) for t in await T.select()]
    return result


@get("/tags/{tag_id:uuid}")
async def get_tag(tag_id: UUID) -> Tag:
    return _to_tag(await _get_or_404(tag_id))


@put("/tags/{tag_id:uuid}")
async def update_tag(tag_id: UUID, data: Tag) -> Tag:
    await _get_or_404(tag_id)
    await T.update({T.name: data.name}).where(T.id == tag_id)
    data.id = tag_id
    return data


@delete("/tags/{tag_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: UUID) -> None:
    await _get_or_404(tag_id)
    await T.delete().where(T.id == tag_id)


tag_api_router = Router(
    path="",
    route_handlers=[create_tag, list_tags, get_tag, update_tag, delete_tag],
    guards=[bearer_token_guard],
    security=[{"BearerAuth": []}],
)
