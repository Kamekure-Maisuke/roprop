from uuid import UUID
from litestar import Router, get
from litestar.response import Template
from sqlalchemy import select

from app.database import get_session
from models import DepartmentModel, EmployeeModel, PCModel


@get("/dashboard")
async def view_dashboard() -> Template:
    """View resource statistics dashboard."""
    with get_session() as session:
        departments_result = session.execute(select(DepartmentModel)).scalars().all()
        employees_result = session.execute(select(EmployeeModel)).scalars().all()
        pcs_result = session.execute(select(PCModel)).scalars().all()

        dept_stats: dict[UUID, dict[str, str | int]] = {}
        unassigned_pc_count = 0

        for dept in departments_result:
            dept_stats[dept.id] = {
                "name": dept.name,
                "employee_count": 0,
                "pc_count": 0,
            }

        for emp in employees_result:
            if emp.department_id and emp.department_id in dept_stats:
                count = dept_stats[emp.department_id]["employee_count"]
                assert isinstance(count, int)
                dept_stats[emp.department_id]["employee_count"] = count + 1

        employees_dict = {e.id: e for e in employees_result}
        for pc in pcs_result:
            if pc.assigned_to:
                emp = employees_dict.get(pc.assigned_to)
                if emp and emp.department_id and emp.department_id in dept_stats:
                    count = dept_stats[emp.department_id]["pc_count"]
                    assert isinstance(count, int)
                    dept_stats[emp.department_id]["pc_count"] = count + 1
            else:
                unassigned_pc_count += 1

        return Template(
            template_name="dashboard.html",
            context={
                "dept_stats": list(dept_stats.values()),
                "unassigned_pc_count": unassigned_pc_count,
                "total_pcs": len(pcs_result),
                "total_employees": len(employees_result),
                "total_departments": len(departments_result),
            },
        )


dashboard_web_router = Router(
    path="",
    route_handlers=[view_dashboard],
)
