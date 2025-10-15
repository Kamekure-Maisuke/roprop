from datetime import date, timedelta
from uuid import UUID

from litestar import Router, get
from litestar.response import Template

from app.auth import session_auth_guard
from app.cache import get_cached, set_cached
from models import DepartmentTable as D, EmployeeTable as E, PCTable as P


@get("/dashboard")
async def view_dashboard() -> Template:
    if cached := await get_cached("dashboard:stats"):
        return Template(template_name="dashboard.html", context=cached)

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

    # アラート取得(7日以内)
    today = date.today()
    target_date = today + timedelta(days=7)
    alerts = {"resignations": [], "transfers": []}

    # PC割り当て状況を取得
    pc_assignments = {pc["assigned_to"]: pc for pc in pcs if pc["assigned_to"]}

    for emp in employees:
        has_pc = emp["id"] in pc_assignments
        if emp["resignation_date"] and today <= emp["resignation_date"] <= target_date:
            alerts["resignations"].append(
                {
                    "name": emp["name"],
                    "date": emp["resignation_date"].isoformat(),
                    "days_left": (emp["resignation_date"] - today).days,
                    "returned": not has_pc,
                }
            )
        if emp["transfer_date"] and today <= emp["transfer_date"] <= target_date:
            alerts["transfers"].append(
                {
                    "name": emp["name"],
                    "date": emp["transfer_date"].isoformat(),
                    "days_left": (emp["transfer_date"] - today).days,
                    "returned": not has_pc,
                }
            )

    context = {
        "dept_stats": list(dept_stats.values()),
        "unassigned_pc_count": unassigned_pc_count,
        "total_pcs": len(pcs),
        "total_employees": len(employees),
        "total_departments": len(departments),
        "alerts": alerts,
    }
    await set_cached("dashboard:stats", context)
    return Template(template_name="dashboard.html", context=context)


dashboard_web_router = Router(
    path="",
    route_handlers=[view_dashboard],
    guards=[session_auth_guard],
)
