from datetime import date, timedelta
from uuid import UUID

from litestar import Router, get
from litestar.response import Template

from app.auth import session_auth_guard
from app.cache import get_cached, set_cached
from models import (
    BlogLikeTable as BLT,
)
from models import (
    BlogPostTable as B,
)
from models import (
    DepartmentTable as D,
)
from models import (
    EmployeeTable as E,
)
from models import (
    PCTable as P,
)


@get("/dashboard")
async def view_dashboard() -> Template:
    if cached := await get_cached("dashboard:stats"):
        return Template(template_name="dashboard.html", context=cached)

    departments = await D.select()
    employees = await E.select(E.all_columns())
    pcs = await P.select(P.all_columns())

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

    # ブログ統計: 投稿数トップ5
    blog_posts = await B.select()
    author_post_counts: dict[UUID, int] = {}
    for post in blog_posts:
        author_id = post["author_id"]
        author_post_counts[author_id] = author_post_counts.get(author_id, 0) + 1

    top_authors = sorted(author_post_counts.items(), key=lambda x: x[1], reverse=True)[
        :5
    ]
    top_authors_data = []
    if top_authors:
        author_ids = [author_id for author_id, _ in top_authors]
        authors_info = {
            e["id"]: e["name"]
            for e in await E.select(E.id, E.name).where(E.id.is_in(author_ids))
        }
        top_authors_data = [
            {"name": authors_info.get(author_id, "不明"), "count": count}
            for author_id, count in top_authors
        ]

    # ブログ統計: いいね数トップ5
    blog_ids = [post["id"] for post in blog_posts]
    blog_like_counts: dict[UUID, int] = {}
    if blog_ids:
        likes = await BLT.select(BLT.blog_post_id).where(
            BLT.blog_post_id.is_in(blog_ids)
        )
        for like in likes:
            blog_id = like["blog_post_id"]
            blog_like_counts[blog_id] = blog_like_counts.get(blog_id, 0) + 1

    top_liked_blogs = sorted(
        blog_like_counts.items(), key=lambda x: x[1], reverse=True
    )[:5]
    top_liked_data = []
    if top_liked_blogs:
        blogs_dict = {post["id"]: post["title"] for post in blog_posts}
        top_liked_data = [
            {"title": blogs_dict.get(blog_id, "不明")[:30], "likes": likes}
            for blog_id, likes in top_liked_blogs
        ]

    context = {
        "dept_stats": list(dept_stats.values()),
        "unassigned_pc_count": unassigned_pc_count,
        "total_pcs": len(pcs),
        "total_employees": len(employees),
        "total_departments": len(departments),
        "alerts": alerts,
        "total_blog_posts": len(blog_posts),
        "total_blog_likes": sum(blog_like_counts.values()),
        "top_authors": top_authors_data,
        "top_liked_blogs": top_liked_data,
    }
    await set_cached("dashboard:stats", context)
    return Template(template_name="dashboard.html", context=context)


dashboard_web_router = Router(
    path="",
    route_handlers=[view_dashboard],
    guards=[session_auth_guard],
)
