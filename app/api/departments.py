from uuid import UUID
from litestar import Router, get, post, put, delete
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from sqlalchemy import select

from app.database import get_session
from models import Department, DepartmentModel


@post("/departments", status_code=HTTP_201_CREATED)
async def create_department(data: Department) -> Department:
    """Create a new department."""
    with get_session() as session:
        department_model = DepartmentModel(
            id=data.id,
            name=data.name,
        )
        session.add(department_model)
        session.commit()

    return data


@get("/departments")
async def list_departments() -> list[Department]:
    """Get all departments."""
    with get_session() as session:
        stmt = select(DepartmentModel)
        results = session.execute(stmt).scalars().all()
        return [
            Department(id=d.id, name=d.name)
            for d in results
        ]


@get("/departments/{department_id:uuid}")
async def get_department(department_id: UUID) -> Department:
    """Get a specific department by ID."""
    with get_session() as session:
        department_model = session.get(DepartmentModel, department_id)
        if not department_model:
            raise NotFoundException(detail=f"Department with ID {department_id} not found")
        return Department(id=department_model.id, name=department_model.name)


@put("/departments/{department_id:uuid}")
async def update_department(department_id: UUID, data: Department) -> Department:
    """Update an existing department."""
    with get_session() as session:
        department_model = session.get(DepartmentModel, department_id)
        if not department_model:
            raise NotFoundException(detail=f"Department with ID {department_id} not found")

        department_model.name = data.name
        session.commit()

    data.id = department_id
    return data


@delete("/departments/{department_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_department(department_id: UUID) -> None:
    """Delete an department."""
    with get_session() as session:
        department_model = session.get(DepartmentModel, department_id)
        if not department_model:
            raise NotFoundException(detail=f"Department with ID {department_id} not found")
        session.delete(department_model)
        session.commit()


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
