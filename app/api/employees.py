from datetime import date, timedelta
from uuid import UUID

from litestar import Router, delete, get, post, put
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException, ValidationException
from litestar.params import Body
from litestar.response import Response
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.auth import bearer_token_guard
from app.cache import delete_cached, get_cached, set_cached
from app.utils import process_profile_image
from models import Employee, EmployeeTable as E, Role


async def _get_or_404(employee_id: UUID) -> dict:
    if not (result := await E.select().where(E.id == employee_id).first()):
        raise NotFoundException(detail=f"Employee with ID {employee_id} not found")
    return result


def _to_employee(data: dict, include_image: bool = False) -> Employee:
    return Employee(
        id=data["id"],
        name=data["name"],
        email=data["email"],
        department_id=data["department_id"],
        profile_image=data.get("profile_image") if include_image else None,
        resignation_date=data.get("resignation_date"),
        transfer_date=data.get("transfer_date"),
        role=Role(data.get("role", Role.USER.value)),
    )


@post("/employees", status_code=HTTP_201_CREATED)
async def create_employee(data: Employee) -> Employee:
    await E(
        id=data.id,
        name=data.name,
        email=data.email,
        department_id=data.department_id,
        resignation_date=data.resignation_date,
        transfer_date=data.transfer_date,
        role=data.role.value,
    ).save()
    await delete_cached("employees:list", "dashboard:stats")
    return data


@get("/employees")
async def list_employees() -> list[Employee]:
    if cached := await get_cached("employees:list"):
        return [Employee(**e) for e in cached]
    result = [_to_employee(e) for e in await E.select()]
    await set_cached("employees:list", [e.__dict__ for e in result])
    return result


@get("/employees/{employee_id:uuid}")
async def get_employee(employee_id: UUID) -> Employee:
    return _to_employee(await _get_or_404(employee_id))


@put("/employees/{employee_id:uuid}")
async def update_employee(employee_id: UUID, data: Employee) -> Employee:
    await _get_or_404(employee_id)
    await E.update(
        {
            E.name: data.name,
            E.email: data.email,
            E.department_id: data.department_id,
            E.resignation_date: data.resignation_date,
            E.transfer_date: data.transfer_date,
            E.role: data.role.value,
        }
    ).where(E.id == employee_id)
    await delete_cached("employees:list", "dashboard:stats")
    data.id = employee_id
    return data


@delete("/employees/{employee_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_employee(employee_id: UUID) -> None:
    await _get_or_404(employee_id)
    await E.delete().where(E.id == employee_id)
    await delete_cached("employees:list", "dashboard:stats")


@post("/employees/{employee_id:uuid}/profile-image", status_code=HTTP_204_NO_CONTENT)
async def upload_profile_image(
    employee_id: UUID,
    data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
) -> None:
    await _get_or_404(employee_id)
    raw = await data.read()
    try:
        processed = process_profile_image(raw)
    except ValueError as e:
        raise ValidationException(detail=str(e))
    await E.update({E.profile_image: processed}).where(E.id == employee_id)


@get("/employees/{employee_id:uuid}/profile-image")
async def get_profile_image(employee_id: UUID) -> Response:
    emp = await _get_or_404(employee_id)
    if not (img := emp.get("profile_image")):
        raise NotFoundException(detail="プロフィール画像が登録されていません")
    return Response(content=bytes(img), media_type="image/webp")


@get("/employees/alerts/upcoming")
async def get_upcoming_alerts(days: int = 7) -> dict:
    """今日から指定日数以内の退職・異動予定がある社員を取得"""
    today = date.today()
    target_date = today + timedelta(days=days)

    employees = await E.select()
    alerts = {"resignations": [], "transfers": []}

    for emp in employees:
        if emp["resignation_date"] and today <= emp["resignation_date"] <= target_date:
            alerts["resignations"].append(_to_employee(emp))
        if emp["transfer_date"] and today <= emp["transfer_date"] <= target_date:
            alerts["transfers"].append(_to_employee(emp))

    return alerts


employee_api_router = Router(
    path="",
    route_handlers=[
        create_employee,
        list_employees,
        get_employee,
        update_employee,
        delete_employee,
        upload_profile_image,
        get_profile_image,
        get_upcoming_alerts,
    ],
    guards=[bearer_token_guard],
    security=[{"BearerAuth": []}],
)
