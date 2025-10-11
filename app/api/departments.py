from uuid import UUID
from litestar import Router, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from models import Department, DepartmentTable as D


async def _get_or_404(department_id: UUID) -> dict:
    """部署を取得、存在しなければ404エラー"""
    if not (result := await D.select().where(D.id == department_id).first()):
        raise NotFoundException(detail=f"Department with ID {department_id} not found")
    return result


def _to_department(data: dict) -> Department:
    """辞書からDepartmentオブジェクトに変換"""
    return Department(id=data["id"], name=data["name"])


@post("/departments", status_code=HTTP_201_CREATED)
async def create_department(data: Department) -> Department:
    await D(id=data.id, name=data.name).save()
    return data


@get("/departments")
async def list_departments() -> list[Department]:
    return [_to_department(d) for d in await D.select()]


@get("/departments/{department_id:uuid}")
async def get_department(department_id: UUID) -> Department:
    return _to_department(await _get_or_404(department_id))


@put("/departments/{department_id:uuid}")
async def update_department(department_id: UUID, data: Department) -> Department:
    await _get_or_404(department_id)
    await D.update({D.name: data.name}).where(D.id == department_id)
    data.id = department_id
    return data


@delete("/departments/{department_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_department(department_id: UUID) -> None:
    await _get_or_404(department_id)
    await D.delete().where(D.id == department_id)


department_api_router = Router(
    path="",
    route_handlers=[
        create_department,
        list_departments,
        get_department,
        update_department,
        delete_department,
    ],
)
