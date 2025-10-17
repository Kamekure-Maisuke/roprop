from litestar import Request, Router, get
from litestar.response import Template

from app.auth import session_auth_guard
from models import BlogPostTable as B, EmployeeTable as E, PCTable as P


@get("/search/view")
async def view_search(request: Request, q: str = "") -> Template:
    results = []
    if q.strip():
        # PC検索
        pcs = await P.raw(
            "SELECT * FROM pcs WHERE ARRAY[name, model, serial_number] &@~ {}",
            q,
        )
        results.extend(
            [
                {
                    "type": "pc",
                    "id": pc["id"],
                    "title": f"PC: {pc['name']}",
                    "description": f"{pc['model']} ({pc['serial_number']})",
                    "link": f"/pcs/{pc['id']}/show",
                }
                for pc in pcs
            ]
        )

        # 社員検索
        employees = await E.raw(
            "SELECT * FROM employees WHERE ARRAY[name, email] &@~ {}", q
        )
        results.extend(
            [
                {
                    "type": "employee",
                    "id": emp["id"],
                    "title": f"社員: {emp['name']}",
                    "description": emp["email"],
                    "link": f"/employees/{emp['id']}/show",
                }
                for emp in employees
            ]
        )

        # ブログ検索
        blogs = await B.raw(
            "SELECT * FROM blog_posts WHERE ARRAY[title, content] &@~ {}", q
        )
        results.extend(
            [
                {
                    "type": "blog",
                    "id": blog["id"],
                    "title": f"ブログ: {blog['title']}",
                    "description": blog["content"][:100] + "..."
                    if len(blog["content"]) > 100
                    else blog["content"],
                    "link": f"/blogs/{blog['id']}/detail",
                }
                for blog in blogs
            ]
        )

    return Template(
        "search.html",
        context={
            "query": q,
            "results": results,
            "user_id": request.state.user_id,
            "user_role": request.state.role.value,
        },
    )


search_web_router = Router(
    path="", route_handlers=[view_search], guards=[session_auth_guard]
)
