from uuid import UUID
from litestar import Router, get, post, put, delete
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from sqlalchemy import select

from app.database import get_session
from models import Employee, EmployeeModel


@post("/employees", status_code=HTTP_201_CREATED)
async def create_employee(data: Employee) -> Employee:
    """Create a new employee."""
    with get_session() as session:
        employee_model = EmployeeModel(
            id=data.id,
            name=data.name,
            email=data.email,
            department_id=data.department_id,
        )
        session.add(employee_model)
        session.commit()

    return data


@get("/employees")
async def list_employees() -> list[Employee]:
    """Get all employees."""
    with get_session() as session:
        stmt = select(EmployeeModel)
        results = session.execute(stmt).scalars().all()
        return [
            Employee(id=e.id, name=e.name, email=e.email, department_id=e.department_id)
            for e in results
        ]


@get("/employees/{employee_id:uuid}")
async def get_employee(employee_id: UUID) -> Employee:
    """Get a specific employee by ID."""
    with get_session() as session:
        employee_model = session.get(EmployeeModel, employee_id)
        if not employee_model:
            raise NotFoundException(detail=f"Employee with ID {employee_id} not found")
        return Employee(
            id=employee_model.id,
            name=employee_model.name,
            email=employee_model.email,
            department_id=employee_model.department_id,
        )


@put("/employees/{employee_id:uuid}")
async def update_employee(employee_id: UUID, data: Employee) -> Employee:
    """Update an existing employee."""
    with get_session() as session:
        employee_model = session.get(EmployeeModel, employee_id)
        if not employee_model:
            raise NotFoundException(detail=f"Employee with ID {employee_id} not found")

        employee_model.name = data.name
        employee_model.email = data.email
        employee_model.department_id = data.department_id

        session.commit()

    data.id = employee_id
    return data


@delete("/employees/{employee_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_employee(employee_id: UUID) -> None:
    """Delete an employee."""
    with get_session() as session:
        employee_model = session.get(EmployeeModel, employee_id)
        if not employee_model:
            raise NotFoundException(detail=f"Employee with ID {employee_id} not found")
        session.delete(employee_model)
        session.commit()


employee_api_router = Router(
    path="",
    route_handlers=[
        create_employee,
        list_employees,
        get_employee,
        update_employee,
        delete_employee,
    ],
)
