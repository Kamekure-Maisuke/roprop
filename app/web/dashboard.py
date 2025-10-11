from uuid import UUID
from litestar import Router, get
from litestar.response import Template

from models import DepartmentTable as D, EmployeeTable as E, PCTable as P


@get("/dashboard")
async def view_dashboard() -> Template:
    departments = await D.select()
    employees = await E.select()
    pcs = await P.select()

    dept_stats: dict[UUID, dict[str, str | int]] = {
        d["id"]: {"name": d["name"], "employee_count": 0, "pc_count": 0}
        for d in departments
    }

    for emp in employees:
        if emp["department_id"] and emp["department_id"] in dept_stats:
            dept_stats[emp["department_id"]]["employee_count"] += 1

    employees_dict = {e["id"]: e for e in employees}
    unassigned_pc_count = 0
    for pc in pcs:
        if (
            pc["assigned_to"]
            and (emp := employees_dict.get(pc["assigned_to"]))
            and emp["department_id"] in dept_stats
        ):
            dept_stats[emp["department_id"]]["pc_count"] += 1
        elif not pc["assigned_to"]:
            unassigned_pc_count += 1

    return Template(
        template_name="dashboard.html",
        context={
            "dept_stats": list(dept_stats.values()),
            "unassigned_pc_count": unassigned_pc_count,
            "total_pcs": len(pcs),
            "total_employees": len(employees),
            "total_departments": len(departments),
        },
    )


dashboard_web_router = Router(
    path="",
    route_handlers=[view_dashboard],
)
